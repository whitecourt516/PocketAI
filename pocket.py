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

from core.executor import execute_command

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
from core.websocket_server import websocket_module
from core.logger import log, logger_module
from core.llm import (
    session_history,
    handle_user_input_sync,
)
from core.avatar_router import send_to_avatar

from pathlib import Path

from core.config_loader import is_read_allowed

from core.executor import execute_command

from core.backup_manager import restore_latest_backup

from core.event_bus import bus

from core.logger import log, logger_module
# ═════════════════════════════════════════════════════════════════════════════
# CLI — text input loop
# ═════════════════════════════════════════════════════════════════════════════

def cli_input_loop():
    print("\nType a message or hold F9 to speak.")
    print("Commands: /quit  /clear  /memory  /load <file>  /read <file>\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  [Pocket signing off. Later user.]\n")
            log.info("pocket", "Pocket signing off")
            os._exit(0)

        if not user_input:
            continue

        if user_input.lower() in ("/quit", "quit", "exit", "bye"):
            print("\n  [Pocket signing off. Later user.]\n")
            log.info("pocket", "Pocket signing off")
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

        if user_input.lower().startswith("/read "):
            filepath = user_input[6:].strip()
            path = (
                Path(filepath)
                if Path(filepath).is_absolute()
                else Path(project_root) / filepath
            )

            if not is_read_allowed(str(path)):
                print(f"  [/read blocked: {filepath} is on the denylist]\n")
                continue

            try:
                content = path.read_text(encoding="utf-8")

                print(f"  [Loaded: {path} ({len(content)} chars)]\n")

                handle_user_input_sync(
                    f"I'm showing you this file: {filepath}\n\n```\n{content}\n```"
                )

            except FileNotFoundError:
                print(f"  [File not found: {path}]\n")

            except Exception as e:
                print(f"  [/read error: {e}]\n")

            continue


        if user_input.lower().startswith("/exec "):
            command = user_input[6:].strip()

            if not command:
                print("  [/exec requires a command]\n")
                continue

            print(f"  [Executing: {command}]\n")

            result = execute_command(command)

            print(result)
            print()

            continue


        if user_input.lower().startswith("/rollback "):
            filepath = user_input[10:].strip()

            if not filepath:
                print("  [/rollback requires a filepath]\n")
                continue

            path = (
                Path(filepath)
                if Path(filepath).is_absolute()
                else Path(project_root) / filepath
            )

            try:
                result = restore_latest_backup(str(path))
                print(f"  {result}\n")
            except Exception as e:
                print(f"  [/rollback error: {e}]\n")

            continue


        handle_user_input_sync(user_input)

# ═════════════════════════════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════════════════════════════

def main():
    print("\n╔══════════════════════════════════╗")
    print("║   Pocket is online. Hey user.   ║")
    print("╚══════════════════════════════════╝\n")

    logger_module.start()
    log.info("pocket", "Pocket starting up")

    bootstrap_knowledge()
    init_whisper()
    websocket_module.start()

    bus.subscribe("connection.websocket.connected",    logger_module.on_event)
    bus.subscribe("connection.websocket.disconnected", logger_module.on_event)
    bus.subscribe("connection.websocket.reconnecting", logger_module.on_event)
    bus.subscribe("connection.websocket.degraded",     logger_module.on_event)

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