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

import json
import os
import sys
import threading

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
    tts_worker,
)
from core.stt import (
    init_whisper,
    keyboard_listener,
)
from core.websocket_server import (
    start_avatar_connection,
)
from core.llm import (
    session_history,
    handle_user_input_sync,
)
from core.avatar_router import send_to_avatar
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