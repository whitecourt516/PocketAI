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
    memory_module,
    save_memory,
    get_relevant_memories,
    load_knowledge_file,
    bootstrap_knowledge,
)
from core.tts import (
    tts_queue,
    tts_module,
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
    llm_module,
    handle_user_input_sync,
)
from core.avatar_router import send_to_avatar
from core.health_check import run_startup_checks
from core.monitor import create_monitor
from core.debug_overlay import DebugOverlay
from pathlib import Path
from core.config_loader import is_read_allowed
from core.executor import execute_command
from core.backup_manager import restore_latest_backup
from core.event_bus import bus
from core.degradation import on_websocket_degraded, on_websocket_connected
from core.logger import log, logger_module
from core.web_search import search, format_for_llm
from core.file_editor import safe_write

monitor = None  # set in main(), read in cli_input_loop() for cleanup
overlay = None  # set in main(), read in cli_input_loop() for cleanup

def altd_listener():
    """Alt+D hotkey — prints a one-shot debug overlay snapshot."""
    from pynput import keyboard
    alt_held = False

    def on_press(key):
        nonlocal alt_held
        if key in (keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r):
            alt_held = True
        elif alt_held and hasattr(key, 'char') and key.char == 'd':
            if overlay:
                overlay.toggle_live()

    def on_release(key):
        nonlocal alt_held
        if key in (keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r):
            alt_held = False

    try:
        with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
            listener.join()
    except Exception as e:
        print(f"  [Alt+D listener error: {e}]")


# ═════════════════════════════════════════════════════════════════════════════
# CLI — text input loop
# ═════════════════════════════════════════════════════════════════════════════

def cli_input_loop():
    print("\nType a message or hold F9 to speak.")
    print("Commands: /quit  /clear  /memory  /load <file>  /read <file>  /search <query>  /edit <file>\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            if overlay:
                overlay.stop()
            if monitor:
                monitor.stop()
            websocket_module.stop()
            log.info("pocket", "Pocket signing off")
            logger_module.stop()    
            print("\n  [Pocket signing off. Later user.]\n")
            os._exit(0)

        if not user_input:
            continue

        if user_input.lower() in ("/quit", "quit", "exit", "bye"):
            if overlay:
                overlay.stop()
            if monitor:
                monitor.stop()
            websocket_module.stop()
            log.info("pocket", "Pocket signing off")
            logger_module.stop()
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
        if user_input.lower().startswith("/edit "):
            filepath = user_input[6:].strip()

            if not filepath:
                print("  [/edit requires a filepath]\n")
                continue

            print(f"  [Editing: {filepath}]")
            print("  Paste the new file content. End with a line containing only:  END\n")

            lines = []
            cancelled = False
            while True:
                try:
                    line = input()
                except (EOFError, KeyboardInterrupt):
                    cancelled = True
                    break
                if line.strip() == "END":
                    break
                lines.append(line)

            if cancelled:
                print("\n  [/edit cancelled]\n")
                continue

            result = safe_write(filepath, "\n".join(lines))
            print(f"  {result}\n")

            continue
        if user_input.lower().startswith("/search "):
            query = user_input[8:].strip()

            if not query:
                print("  [/search requires a query]\n")
                continue

            print(f"  [Searching the web for: {query}]\n")

            # user typed this himself — his invocation is the approval.
            result = search(query, require_approval=False)

            if not result["ok"]:
                print(f"  [/search failed: {result['error']}]\n")
                continue

            handle_user_input_sync(
                f"I searched the web for: {query}\n\n"
                f"Here are the results:\n\n{format_for_llm(result)}"
            )

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

    bus.subscribe("connection.websocket.degraded",  on_websocket_degraded)
    bus.subscribe("connection.websocket.connected", on_websocket_connected)

    # TTS worker thread
    tts_thread = threading.Thread(target=tts_worker, daemon=True)
    tts_thread.start()

    # F9 keyboard listener thread
    kb_thread = threading.Thread(
        target=keyboard_listener, args=(handle_user_input_sync,), daemon=True
    )
    kb_thread.start()

    # Startup health checks (Stage 4j)
    modules = {
        "llm":    llm_module,
        "memory": memory_module,
        "tts":    tts_module,
        "ws":     websocket_module,
    }
    if not run_startup_checks(modules, send_to_avatar):
        sys.exit(1)

    # Continuous self-monitoring (Stage 4j.1)
    global monitor
    monitor = create_monitor(modules, send_to_avatar_fn=send_to_avatar)
    monitor.start()

    # Runtime debug overlay (Stage 4t)
    global overlay
    overlay = DebugOverlay(send_to_avatar_fn=websocket_module.send)

    # Alt+D hotkey thread
    altd_thread = threading.Thread(target=altd_listener, daemon=True)
    altd_thread.start()

    # CLI runs on main thread
    cli_input_loop()


if __name__ == "__main__":
    main()