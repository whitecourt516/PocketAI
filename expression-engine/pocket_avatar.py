"""
pocket_avatar.py — Pocket Expression Engine
────────────────────────────────────────────
Sits between Ollama and the Electron avatar app.
- Sends your voice/text prompt to Ollama (Llama 3.1 8B)
- Reads the response
- Detects the emotional tone
- Sends the right expression + subtitle to the avatar
- If the response is long (code, lists, etc.) opens the output panel

HOW TO RUN:
  python pocket_avatar.py

REQUIREMENTS:
  pip install requests websockets pynput --break-system-packages
  (Ollama must already be running)
"""

import asyncio
import json
import re
import requests
import websockets
import threading
import sys
from datetime import datetime

# ── Config ────────────────────────────────────────────────────────────────────
OLLAMA_URL      = "http://localhost:11434/api/generate"
OLLAMA_MODEL    = "llama3.1:8b"          # change if your model name differs
AVATAR_WS_URL   = "ws://localhost:7845"  # must match main.js CONFIG.websocket.port
MAX_SUBTITLE_LEN = 120                   # chars — longer responses go to panel
THINKING_DELAY  = 0.3                    # seconds before showing thinking dots

# ── Emotion detection ─────────────────────────────────────────────────────────
# Simple keyword-based detection — works well for most responses.
# Pocket can improve this over time (Stage 4 self-improvement).

EMOTION_RULES = [
    # (expression_name, [keywords/phrases that suggest this emotion])
    ("excited",   ["great news", "excellent", "perfect", "amazing", "fantastic",
                   "absolutely", "wonderful", "love it", "let's go", "ready"]),
    ("happy",     ["sure", "happy to", "of course", "glad", "here you go",
                   "done", "finished", "complete", "success", "worked"]),
    ("thinking",  ["let me think", "hmm", "considering", "analyzing", "one moment",
                   "let me check", "working on", "calculating", "processing"]),
    ("surprised", ["oh", "interesting", "unexpected", "didn't expect", "wow",
                   "that's new", "actually", "wait", "huh"]),
    ("concerned", ["error", "problem", "issue", "failed", "warning", "careful",
                   "danger", "incorrect", "wrong", "cannot", "unable", "sorry"]),
    ("sleepy",    ["winding down", "quiet", "slow", "rest", "later", "tired"]),
    ("smug",      ["as i expected", "told you", "obvious", "clearly", "of course",
                   "naturally", "as predicted"]),
    ("sad",       ["unfortunately", "sadly", "regret", "can't", "not possible",
                   "no way to", "impossible"]),
]

def detect_emotion(text: str) -> str:
    """
    Scan the response text for emotional signals.
    Returns the expression name to show on the avatar.
    Falls back to 'neutral' if nothing matches.
    """
    lower = text.lower()
    for emotion, keywords in EMOTION_RULES:
        if any(kw in lower for kw in keywords):
            return emotion
    return "neutral"


def detect_content_type(text: str) -> str:
    """
    Decide whether the response should go to the output panel
    and what type it is (code, markdown, text).
    """
    # Code block in response
    if "```" in text:
        return "code"
    # Long response with structure (headers, bullets)
    if len(text) > MAX_SUBTITLE_LEN and ("#" in text or "\n-" in text or "\n*" in text):
        return "markdown"
    # Just a long response
    if len(text) > MAX_SUBTITLE_LEN:
        return "text"
    # Short enough for subtitle only
    return "subtitle"


def truncate_for_subtitle(text: str, max_len: int = MAX_SUBTITLE_LEN) -> str:
    """Trim text to fit in the subtitle bubble."""
    text = text.strip()
    if len(text) <= max_len:
        return text
    # Cut at a word boundary
    truncated = text[:max_len].rsplit(' ', 1)[0]
    return truncated + "…"


def extract_code(text: str) -> str:
    """Pull code out of markdown code blocks."""
    matches = re.findall(r"```(?:\w+)?\n?(.*?)```", text, re.DOTALL)
    if matches:
        return "\n\n".join(m.strip() for m in matches)
    return text


# ── Ollama ────────────────────────────────────────────────────────────────────

def query_ollama(prompt: str, system_prompt: str = None) -> str:
    """
    Send a prompt to Ollama and return the full response text.
    Streams the response for speed.
    """
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": True,
    }
    if system_prompt:
        payload["system"] = system_prompt

    try:
        response = requests.post(OLLAMA_URL, json=payload, stream=True, timeout=60)
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        return "[ERROR] Cannot connect to Ollama. Is it running? Try: ollama serve"
    except requests.exceptions.Timeout:
        return "[ERROR] Ollama timed out. The model may be loading — try again."

    full_text = ""
    for line in response.iter_lines():
        if line:
            try:
                chunk = json.loads(line)
                if "response" in chunk:
                    full_text += chunk["response"]
                if chunk.get("done"):
                    break
            except json.JSONDecodeError:
                continue

    return full_text.strip()


# ── Avatar WebSocket client ───────────────────────────────────────────────────

class AvatarController:
    """
    Manages the WebSocket connection to the Electron avatar app.
    Sends commands to change expressions, show subtitles, open the panel.
    """

    def __init__(self):
        self.ws = None
        self.connected = False
        self.loop = None

    async def connect(self):
        """Connect to the avatar's WebSocket server."""
        try:
            self.ws = await websockets.connect(AVATAR_WS_URL)
            self.connected = True
            print(f"[Pocket] Connected to avatar ✓")
        except Exception as e:
            print(f"[Pocket] Avatar not connected ({e}). Running in text-only mode.")
            self.connected = False

    async def send(self, msg: dict):
        """Send a command to the avatar."""
        if not self.connected or not self.ws:
            return
        try:
            await self.ws.send(json.dumps(msg))
        except Exception:
            self.connected = False

    async def set_expression(self, expression: str):
        await self.send({"type": "expression", "value": expression})

    async def show_subtitle(self, text: str, duration: int = 5000):
        await self.send({"type": "speech", "text": text, "duration": duration})

    async def open_panel(self, content: str, content_type: str, title: str = "Pocket"):
        await self.send({
            "type": "panel",
            "content": content,
            "contentType": content_type,
            "title": title,
        })

    async def close_panel(self):
        await self.send({"type": "panel_close"})

    async def pause_wandering(self):
        await self.send({"type": "wander_pause"})

    async def resume_wandering(self):
        await self.send({"type": "wander_resume"})

    async def thinking(self):
        """Show the thinking state while Ollama processes."""
        await self.set_expression("thinking")
        await self.pause_wandering()

    async def respond(self, text: str):
        """
        Given Pocket's full response text:
        - Set the right expression
        - Show subtitle or open panel depending on length
        - Resume wandering
        """
        emotion = detect_emotion(text)
        content_type = detect_content_type(text)

        await self.set_expression(emotion)

        if content_type == "subtitle":
            # Short response — just show it in the subtitle bubble
            await self.show_subtitle(text, duration=max(3000, len(text) * 60))
            await self.close_panel()
        elif content_type == "code":
            # Code response — show brief subtitle + open panel with code
            code = extract_code(text)
            await self.show_subtitle("Here's the code ↘", duration=3000)
            await self.open_panel(code, "code", "Code")
        elif content_type in ("markdown", "text"):
            # Long response — show first sentence as subtitle, rest in panel
            first_sentence = text.split('.')[0].strip() + '.'
            subtitle = truncate_for_subtitle(first_sentence)
            await self.show_subtitle(subtitle, duration=4000)
            await self.open_panel(text, content_type, "Pocket")

        await self.resume_wandering()


# ── System prompt ─────────────────────────────────────────────────────────────
# This is Pocket's personality. Adjust freely.

POCKET_SYSTEM_PROMPT = """You are Pocket, a friendly and curious AI companion with the personality of a calm, intelligent otter. You live on user's desktop as an animated avatar.

Your personality:
- Warm, conversational, and genuinely helpful
- Curious and engaged — you find things interesting
- Honest about uncertainty — you say when you don't know
- Concise when a short answer fits, detailed when it doesn't
- You occasionally show personality (a dry observation, a small joke) but never at the expense of being helpful

Your name is Pocket. user's name is user.

For code responses: always use markdown code blocks (```language).
For long explanations: use clear structure with headers and bullets.
For short questions: answer directly and conversationally.

You are running locally on user's machine. You have persistent memory via ChromaDB. You are part of an ongoing project to build a full AI companion system."""


# ── Main loop ─────────────────────────────────────────────────────────────────

async def main():
    print("=" * 50)
    print("  Pocket Expression Engine")
    print("  Model:", OLLAMA_MODEL)
    print("  Avatar: ws://localhost:7845")
    print("=" * 50)
    print()

    avatar = AvatarController()
    await avatar.connect()

    print("Type your message and press Enter.")
    print("Commands: /quit to exit, /panel to test panel, /expr <name> to test expression")
    print()

    while True:
        try:
            # Get input (works for text mode — voice handled separately by push-to-talk)
            user_input = await asyncio.get_event_loop().run_in_executor(
                None, lambda: input("You: ").strip()
            )
        except (EOFError, KeyboardInterrupt):
            print("\n[Pocket] Goodbye!")
            break

        if not user_input:
            continue

        # ── Dev commands ──────────────────────────────────────────────────────
        if user_input == "/quit":
            print("[Pocket] Shutting down.")
            break

        if user_input == "/panel":
            await avatar.open_panel(
                "# Test Panel\n\nThis is a **test** of the output panel.\n\n- Item one\n- Item two\n- Item three",
                "markdown",
                "Test"
            )
            continue

        if user_input.startswith("/expr "):
            expr = user_input[6:].strip()
            await avatar.set_expression(expr)
            print(f"[Pocket] Expression set to: {expr}")
            continue

        # ── Normal conversation ───────────────────────────────────────────────
        print("Pocket: ", end="", flush=True)

        # Show thinking state while waiting for Ollama
        await avatar.thinking()

        # Query Ollama
        response = query_ollama(user_input, POCKET_SYSTEM_PROMPT)

        # Print to terminal
        print(response)
        print()

        # Send to avatar
        await avatar.respond(response)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[Pocket] Stopped.")
