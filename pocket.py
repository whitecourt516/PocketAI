"""
pocket.py — Pocket Unified Engine
───────────────────────────────────────────────────────────────────────────────
Single script that handles:
  - Push-to-talk voice input (F9) via Whisper
  - Text input fallback via CLI
  - Ollama LLM with session history
  - ChromaDB memory persistence (direct — no HTTP middleman)
  - Piper TTS voice output
  - Avatar expression control via WebSocket
  - Output panel for long/code responses

HOW TO RUN:
  python pocket.py

REQUIREMENTS:
  pip install chromadb ollama whisper sounddevice numpy websockets pynput
"""

import asyncio
import json
import os
import re
import subprocess
import sys
import threading
import time
import uuid
import queue

import numpy as np
import sounddevice as sd
import websockets

from pathlib import Path
from pynput import keyboard

# ── Path setup ────────────────────────────────────────────────────────────────
script_dir   = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(script_dir, '..', '..')
sys.path.insert(0, project_root)

# ── Project imports ───────────────────────────────────────────────────────────
# ── Project imports ───────────────────────────────────────────────────────────
from config.settings import (
    MODEL, COLLECTION_NAME, N_MEMORIES, KNOWLEDGE_FILES,
    WHISPER_MODEL, SAMPLE_RATE, CHANNELS,
    SILENCE_THRESHOLD, SILENCE_DURATION, MAX_RECORD_SECS,
    WEBSOCKET_PORT, TYPING_CHARS_PER_SEC,
)
from config.persona import SYSTEM_PROMPT

from core.memory import (
    memory,
    save_memory,
    get_relevant_memories,
    load_knowledge_file,
    bootstrap_knowledge,
)
from core.tts import (
    tts_queue,
    speaking_flag,
    run_piper_tts,
    tts_worker,
)
from core.stt import (
    recording_flag,
    init_whisper,
    handle_voice_input,
    keyboard_listener,
)

import chromadb
import ollama

# ── Optional imports ──────────────────────────────────────────────────────────
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

try:
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False

# ── Path constants (runtime-derived, stay here not in config/) ────────────────
CHROMA_PATH  = os.path.join(project_root, "chroma_data")
AVATAR_WS_URL = "ws://localhost:3000"

MAX_SUBTITLE_LEN = 120

# ── Runtime clients ───────────────────────────────────────────────────────────
ollama_client = ollama.Client(host=os.getenv("OLLAMA_HOST", "http://localhost:11434"))
# ── Runtime state ─────────────────────────────────────────────────────────────
session_history = []
ws_clients      = set()

# ── Expression engine ─────────────────────────────────────────────────────────
try:
    from avatar.expression_engine import ExpressionEngine
    expression_engine = ExpressionEngine()
    EXPRESSION_ENGINE_AVAILABLE = True
except ImportError:
    expression_engine = None
    EXPRESSION_ENGINE_AVAILABLE = False

# ═════════════════════════════════════════════════════════════════════════════
# AVATAR — WebSocket connection to Electron
# ═════════════════════════════════════════════════════════════════════════════

_avatar_ws        = None
_avatar_connected = False
_loop             = None


async def _avatar_connect():
    global _avatar_ws, _avatar_connected
    try:
        _avatar_ws = await websockets.connect(AVATAR_WS_URL)
        _avatar_connected = True
        print("  [Avatar connected ✓]")
    except Exception as e:
        _avatar_connected = False

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
    time.sleep(0.5)  # Give the loop a moment to start
    asyncio.run_coroutine_threadsafe(_avatar_connect(), _loop)


# ═════════════════════════════════════════════════════════════════════════════
# EMOTION / CONTENT DETECTION
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
    """Route Pocket's reply to the avatar — expression + subtitle or panel."""
    emotion      = detect_emotion(response_text)
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
# LLM — Ollama chat
# ═════════════════════════════════════════════════════════════════════════════

def handle_user_input_sync(text: str):
    """Process user input, get LLM reply, update memory and avatar."""
    global session_history

    avatar_thinking()

    past        = get_relevant_memories(text)
    full_system = SYSTEM_PROMPT + (f"\n\n{past}" if past else "")

    messages = [{"role": "system", "content": full_system}]
    messages += session_history
    messages.append({"role": "user", "content": text})

    try:
        response = ollama_client.chat(model=MODEL, messages=messages)
        reply    = response["message"]["content"]
    except Exception as e:
        reply = f"[LLM error: {e}]"
        print(reply)
        avatar_done_thinking()
        return

    session_history.append({"role": "user",      "content": text})
    session_history.append({"role": "assistant",  "content": reply})

    save_memory("user",      text)
    save_memory("assistant", reply)

    print(f"\nPocket: {reply}\n")

    send_to_avatar(reply)
    tts_queue.put(reply)

# ═════════════════════════════════════════════════════════════════════════════
# CLI — text input loop
# ═════════════════════════════════════════════════════════════════════════════

def cli_input_loop():
    print("\nType a message or hold F9 to speak.")
    print("Commands: /quit  /clear  /memory  /load <file>\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  [Pocket signing off. Later user.]\n")
            os._exit(0)

        if not user_input:
            continue

        if user_input.lower() in ("/quit", "quit", "exit", "bye"):
            print("\n  [Pocket signing off. Later user.]\n")
            os._exit(0)

        if user_input.lower() == "/clear":
            session_history.clear()
            print("  [Session cleared]\n")
            continue

        if user_input.lower() == "/memory":
            print(f"  [Memory: {memory.count()} entries in ChromaDB]\n")
            continue

        if user_input.lower().startswith("/load "):
            load_knowledge_file(user_input[6:].strip())
            continue

        handle_user_input_sync(user_input)


# ═════════════════════════════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════════════════════════════

def main():
    print("\n╔══════════════════════════════════╗")
    print("║   Pocket is online. Hey user.   ║")
    print("╚══════════════════════════════════╝\n")

    bootstrap_knowledge()
    init_whisper()
    start_avatar_connection()

    # TTS worker thread
    tts_thread = threading.Thread(target=tts_worker, daemon=True)
    tts_thread.start()

    # F9 keyboard listener thread
    kb_thread = threading.Thread(
        target=keyboard_listener, args=(handle_user_input_sync,), daemon=True
    )
    kb_thread.start()

    # CLI runs on main thread
    cli_input_loop()


if __name__ == "__main__":
    main()