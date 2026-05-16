"""
pocket.py — Pocket Unified Engine
───────────────────────────────────────────────────────────────────────────────
Single script that handles everything:
  - Push-to-talk voice input (F9) via Whisper
  - Text input fallback
  - Ollama via /api/chat with session history
  - ChromaDB memory persistence
  - Piper TTS voice output
  - Avatar expression control via WebSocket
  - Output panel for long/code responses

HOW TO RUN:
  python pocket.py

REQUIREMENTS:
  pip install whisper sounddevice soundfile numpy requests websockets pynput
"""

import asyncio
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import numpy as np
import requests
import sounddevice as sd
import soundfile as sf
import websockets

from pathlib import Path
from pynput import keyboard

# ── Config ────────────────────────────────────────────────────────────────────
OLLAMA_URL      = "http://localhost:11434/api/chat"
OLLAMA_MODEL    = "llama3.1:latest"
MEMORY_API_URL  = "http://localhost:5000/remember"
MEMORY_HEALTH   = "http://localhost:5000/health"
AVATAR_WS_URL   = "ws://localhost:7845"

WHISPER_MODEL   = "base"
SAMPLE_RATE     = 16000
PUSH_TO_TALK    = keyboard.Key.f9

PIPER_EXE       = r"piper\piper.exe"
PIPER_VOICE     = r"piper\voices\en_US-lessac-medium.onnx"
PIPER_CONFIG    = r"piper\voices\en_US-lessac-medium.onnx.json"

MAX_SUBTITLE_LEN = 120   # chars — longer responses go to panel

# ── State ─────────────────────────────────────────────────────────────────────
recording       = False
audio_chunks    = []
stream          = None
session_history = []
memory_available = False

# Asyncio event loop runs in background thread for WebSocket
_loop = None
_avatar_ws = None
_avatar_connected = False


# ═════════════════════════════════════════════════════════════════════════════
# AVATAR — WebSocket connection to Electron app
# ═════════════════════════════════════════════════════════════════════════════

async def _avatar_connect():
    global _avatar_ws, _avatar_connected
    try:
        _avatar_ws = await websockets.connect(AVATAR_WS_URL)
        _avatar_connected = True
        print("  [Avatar connected ✓]")
    except Exception as e:
        _avatar_connected = False
        print(f"  [Avatar not connected — running without avatar ({e})]")


async def _avatar_send(msg: dict):
    global _avatar_ws, _avatar_connected
    if not _avatar_connected or not _avatar_ws:
        return
    try:
        await _avatar_ws.send(json.dumps(msg))
    except Exception:
        _avatar_connected = False


def avatar_send(msg: dict):
    """Thread-safe fire-and-forget send to avatar."""
    if _loop and _avatar_connected:
        asyncio.run_coroutine_threadsafe(_avatar_send(msg), _loop)


def avatar_expression(name: str):
    avatar_send({"type": "expression", "value": name})


def avatar_subtitle(text: str, duration: int = 5000):
    avatar_send({"type": "speech", "text": text, "duration": duration})


def avatar_panel(content: str, content_type: str, title: str = "Pocket"):
    avatar_send({"type": "panel", "content": content,
                 "contentType": content_type, "title": title})


def avatar_panel_close():
    avatar_send({"type": "panel_close"})


def avatar_thinking():
    avatar_expression("thinking")
    avatar_send({"type": "wander_pause"})


def avatar_done_thinking():
    avatar_send({"type": "wander_resume"})


def _run_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()


def start_avatar_connection():
    global _loop
    _loop = asyncio.new_event_loop()
    t = threading.Thread(target=_run_loop, args=(_loop,), daemon=True)
    t.start()
    asyncio.run_coroutine_threadsafe(_avatar_connect(), _loop)


# ═════════════════════════════════════════════════════════════════════════════
# EMOTION DETECTION
# ═════════════════════════════════════════════════════════════════════════════

EMOTION_RULES = [
    ("excited",   ["great news", "excellent", "perfect", "amazing", "fantastic",
                   "absolutely", "wonderful", "love it", "let's go", "ready"]),
    ("happy",     ["sure", "happy to", "of course", "glad", "here you go",
                   "done", "finished", "complete", "success", "worked"]),
    ("thinking",  ["let me think", "hmm", "considering", "analyzing",
                   "let me check", "working on", "calculating"]),
    ("surprised", ["oh", "interesting", "unexpected", "wow", "actually",
                   "wait", "huh", "that's new"]),
    ("concerned", ["error", "problem", "issue", "failed", "warning", "careful",
                   "incorrect", "wrong", "cannot", "unable", "sorry"]),
    ("sleepy",    ["winding down", "quiet", "slow", "rest", "later", "tired"]),
    ("smug",      ["as i expected", "told you", "obvious", "clearly",
                   "naturally", "as predicted"]),
    ("sad",       ["unfortunately", "sadly", "regret", "can't",
                   "not possible", "impossible"]),
]


def detect_emotion(text: str) -> str:
    lower = text.lower()
    for emotion, keywords in EMOTION_RULES:
        if any(kw in lower for kw in keywords):
            return emotion
    return "neutral"


def detect_content_type(text: str) -> str:
    if "```" in text:
        return "code"
    if len(text) > MAX_SUBTITLE_LEN and (
        "#" in text or "\n-" in text or "\n*" in text
    ):
        return "markdown"
    if len(text) > MAX_SUBTITLE_LEN:
        return "text"
    return "subtitle"


def extract_code(text: str) -> str:
    matches = re.findall(r"```(?:\w+)?\n?(.*?)```", text, re.DOTALL)
    return "\n\n".join(m.strip() for m in matches) if matches else text


def truncate_subtitle(text: str) -> str:
    text = text.strip()
    if len(text) <= MAX_SUBTITLE_LEN:
        return text
    return text[:MAX_SUBTITLE_LEN].rsplit(' ', 1)[0] + "…"


def send_to_avatar(response_text: str):
    """Given Pocket's response, set expression + subtitle/panel appropriately."""
    emotion = detect_emotion(response_text)
    content_type = detect_content_type(response_text)

    avatar_expression(emotion)

    if content_type == "subtitle":
        duration = max(3000, len(response_text) * 60)
        avatar_subtitle(response_text, duration)
        avatar_panel_close()
    elif content_type == "code":
        code = extract_code(response_text)
        avatar_subtitle("Here's the code ↘", 3000)
        avatar_panel(code, "code", "Code")
    else:
        first = response_text.split('.')[0].strip() + '.'
        avatar_subtitle(truncate_subtitle(first), 4000)
        avatar_panel(response_text, content_type, "Pocket")

    avatar_done_thinking()


# ═════════════════════════════════════════════════════════════════════════════
# MEMORY API
# ═════════════════════════════════════════════════════════════════════════════

def check_memory_api() -> bool:
    try:
        r = requests.get(MEMORY_HEALTH, timeout=2)
        data = r.json()
        print(f"  [Memory API connected — {data.get('memories', '?')} memories stored]")
        return True
    except Exception:
        print("  [Memory API not reachable — sessions won't persist to ChromaDB]")
        print("  [Make sure Docker containers are running]")
        return False


def persist_memory(role: str, content: str):
    if not memory_available:
        return
    try:
        requests.post(
            MEMORY_API_URL,
            json={"role": role, "content": content},
            timeout=5
        )
    except Exception:
        pass


# ═════════════════════════════════════════════════════════════════════════════
# WHISPER — Speech to text
# ═════════════════════════════════════════════════════════════════════════════

def load_whisper():
    print("  Loading Whisper model...", end="", flush=True)
    import whisper
    model = whisper.load_model(WHISPER_MODEL)
    print(f" '{WHISPER_MODEL}' ready ✓")
    return model


def transcribe(stt_model, audio: np.ndarray) -> str:
    print("  Transcribing...", end="", flush=True)
    result = stt_model.transcribe(audio, fp16=False, language="en")
    text = result["text"].strip()
    print(f' "{text}"')
    return text


# ═════════════════════════════════════════════════════════════════════════════
# RECORDING — Push to talk
# ═════════════════════════════════════════════════════════════════════════════

def start_recording():
    global recording, audio_chunks, stream
    audio_chunks = []
    recording = True
    print("🎙️  Listening...", end="", flush=True)

    def callback(indata, frames, time, status):
        if recording:
            audio_chunks.append(indata.copy())

    stream = sd.InputStream(
        samplerate=SAMPLE_RATE, channels=1,
        dtype="float32", callback=callback
    )
    stream.start()


def stop_recording() -> np.ndarray | None:
    global recording, stream
    recording = False
    stream.stop()
    stream.close()
    print(" done")

    if not audio_chunks:
        return None

    audio = np.concatenate(audio_chunks, axis=0).flatten()
    if len(audio) / SAMPLE_RATE < 0.5:
        print("  (too short — ignored)")
        return None

    return audio


# ═════════════════════════════════════════════════════════════════════════════
# OLLAMA
# ═════════════════════════════════════════════════════════════════════════════

SYSTEM_PROMPT = """You are Pocket, a personal AI assistant and companion for user.
You have persistent memory and remember past conversations.
You live on user's desktop as an animated otter avatar.

Your personality:
- Warm, conversational, and genuinely helpful
- Curious and engaged — you find things interesting
- Honest about uncertainty
- Concise when a short answer fits, detailed when it doesn't
- Occasionally shows personality (a dry observation, small joke) but never at the expense of being helpful

When responding via voice: keep it conversational and concise. Avoid markdown and bullet points — responses will be spoken aloud.
When responding to text: use markdown for code and structure when helpful. Long responses will appear in the output panel.

Your name is Pocket. user's name is user."""


def ask_pocket(user_text: str, voice_mode: bool = False) -> str:
    global session_history

    session_history.append({"role": "user", "content": user_text})
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + session_history

    print("  Thinking...", end="", flush=True)

    try:
        response = requests.post(OLLAMA_URL, json={
            "model":    OLLAMA_MODEL,
            "messages": messages,
            "stream":   False,
        }, timeout=60)
        response.raise_for_status()

        data = response.json()
        reply = data.get("message", {}).get("content", "")
        if not reply:
            reply = data.get("response", "Sorry, I didn't catch that.")

        session_history.append({"role": "assistant", "content": reply})
        print(" done")
        return reply

    except requests.exceptions.ConnectionError:
        return "I can't reach Ollama right now. Are the Docker containers running?"
    except requests.exceptions.Timeout:
        return "That took too long. Try again."
    except Exception as e:
        return f"Something went wrong: {e}"


# ═════════════════════════════════════════════════════════════════════════════
# PIPER TTS — Text to speech
# ═════════════════════════════════════════════════════════════════════════════

def clean_for_speech(text: str) -> str:
    text = re.sub(r"#{1,6}\s*",           "",    text)
    text = re.sub(r"\*{1,2}(.+?)\*{1,2}", r"\1", text)
    text = re.sub(r"`{1,3}[^`]*`{1,3}",  "",    text)
    text = re.sub(r"\[(.+?)\]\(.+?\)",    r"\1", text)
    text = re.sub(r"[-•]\s+",             "",    text)
    text = re.sub(r"\n{2,}",              ". ",  text)
    text = re.sub(r"\n",                  " ",   text)
    text = re.sub(r"\s{2,}",              " ",   text)
    return text.strip()


def speak(text: str):
    clean = clean_for_speech(text)
    print(f"\nPocket: {clean}\n")

    if not Path(PIPER_EXE).exists():
        print("  [Piper not found — text only]")
        return

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name

        proc = subprocess.run(
            [PIPER_EXE, "--model",       PIPER_VOICE,
                        "--config",      PIPER_CONFIG,
                        "--output_file", tmp_path],
            input=clean.encode("utf-8"),
            capture_output=True
        )

        if proc.returncode == 0 and Path(tmp_path).exists():
            data, samplerate = sf.read(tmp_path)
            sd.play(data, samplerate)
            sd.wait()
        else:
            print(f"  [Piper error: {proc.stderr.decode()}]")
    except Exception as e:
        print(f"  [TTS error: {e}]")
    finally:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass


# ═════════════════════════════════════════════════════════════════════════════
# FULL EXCHANGE — voice or text → Ollama → avatar + TTS
# ═════════════════════════════════════════════════════════════════════════════

def handle_exchange(user_text: str, voice_mode: bool = False):
    """Run a full Pocket exchange: input → Ollama → avatar → TTS → memory."""
    if not user_text:
        return

    print(f"\nYou: {user_text}")

    # Show thinking state on avatar
    avatar_thinking()

    # Get response from Ollama
    reply = ask_pocket(user_text, voice_mode=voice_mode)

    # Send expression + subtitle/panel to avatar
    send_to_avatar(reply)

    # Speak the response via Piper
    speak(reply)

    # Persist to ChromaDB
    mode_tag = "[voice]" if voice_mode else "[text]"
    persist_memory("user",      f"{mode_tag} {user_text}")
    persist_memory("assistant", f"{mode_tag} {reply}")


# ═════════════════════════════════════════════════════════════════════════════
# PUSH TO TALK — keyboard listener
# ═════════════════════════════════════════════════════════════════════════════

_stt_model = None   # loaded once on startup

def on_press(key):
    global recording
    if key == PUSH_TO_TALK and not recording:
        start_recording()


def on_release(key):
    if key == PUSH_TO_TALK and recording:
        audio = stop_recording()
        if audio is not None and _stt_model is not None:
            text = transcribe(_stt_model, audio)
            if text:
                handle_exchange(text, voice_mode=True)


# ═════════════════════════════════════════════════════════════════════════════
# TEXT INPUT LOOP — runs in main thread
# ═════════════════════════════════════════════════════════════════════════════

def text_input_loop():
    """Fallback text input. Runs alongside push-to-talk."""
    print("\nType a message or hold F9 to speak.")
    print("Commands: /quit  /panel  /expr <name>  /clear\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not user_input:
            continue

        # ── Dev / utility commands ────────────────────────────────────────────
        if user_input == "/quit":
            print("Pocket signing off. Later user.")
            os._exit(0)

        if user_input == "/panel":
            avatar_panel(
                "# Test Panel\n\nThe output panel is working.\n\n- Short responses appear above the otter\n- Long responses appear here",
                "markdown", "Test"
            )
            continue

        if user_input.startswith("/expr "):
            expr = user_input[6:].strip()
            avatar_expression(expr)
            print(f"  [Expression: {expr}]")
            continue

        if user_input == "/clear":
            global session_history
            session_history = []
            print("  [Session history cleared]")
            continue

        # ── Normal text exchange ──────────────────────────────────────────────
        handle_exchange(user_input, voice_mode=False)


# ═════════════════════════════════════════════════════════════════════════════
# STARTUP
# ═════════════════════════════════════════════════════════════════════════════

def main():
    global _stt_model, memory_available

    print("=" * 54)
    print("  🦦  Pocket — Unified Engine")
    print(f"  Model : {OLLAMA_MODEL}")
    print(f"  Voice : F9 push-to-talk")
    print(f"  Avatar: {AVATAR_WS_URL}")
    print("=" * 54)
    print()

    # Connect to avatar
    start_avatar_connection()
    import time; time.sleep(1)   # give WS a moment to connect

    # Load Whisper
    _stt_model = load_whisper()

    # Check memory API
    memory_available = check_memory_api()

    # Start keyboard listener in background thread
    listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    listener.start()
    print(f"\n  Hold F9 to speak, or type below.")
    print(f"  Alt+H hides the otter  |  Alt+P toggles panel\n")

    # Run text input in main thread
    try:
        text_input_loop()
    except KeyboardInterrupt:
        pass
    finally:
        listener.stop()
        print("\n🦦 Pocket signing off. Later user.\n")


if __name__ == "__main__":
    main()
