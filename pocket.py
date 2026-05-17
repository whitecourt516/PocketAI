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
project_root = script_dir
sys.path.insert(0, project_root)

# ── Project imports ───────────────────────────────────────────────────────────
from config.settings import (
    MODEL, COLLECTION_NAME, N_MEMORIES, KNOWLEDGE_FILES,
    WHISPER_MODEL, SAMPLE_RATE, CHANNELS,
    SILENCE_THRESHOLD, SILENCE_DURATION, MAX_RECORD_SECS,
    WEBSOCKET_PORT, TYPING_CHARS_PER_SEC,
)

import json

# ── Load system prompt ───────────────────────────────────────────────────────
_prompt_path = os.path.join(
    project_root,
    "persona",
    "prompts",
    "base_system.md"
)

with open(_prompt_path, "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()

_expressions_path = os.path.join(project_root, "config", "expressions.json")
with open(_expressions_path, "r", encoding="utf-8") as f:
    _expressions = json.load(f)
EMOTION_RULES = list(_expressions.items())

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
from core.websocket_server import (
    start_avatar_connection,
    avatar_send,
    avatar_expression,
    avatar_subtitle,
    avatar_panel,
    avatar_panel_close,
    avatar_thinking,
    avatar_done_thinking,
)
from core.llm import (
    session_history,
    handle_user_input_sync,
)
import chromadb

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
MAX_SUBTITLE_LEN = 120

# ── Runtime state ─────────────────────────────────────────────────────────────
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
# EMOTION / CONTENT DETECTION
# ═════════════════════════════════════════════════════════════════════════════

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