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
    memory_module,
    save_memory,
    get_relevant_memories,
    load_knowledge_file,
)
from core.tts import (
    tts_queue,
    tts_module,
    speaking_flag,
)
from core.stt import (
    stt_module,
    keyboard_listener,
)
from core.websocket_server import websocket_module, send_dict_to_avatar
from core.logger import log, logger_module
from core.llm import (
    llm_module,
    handle_user_input_sync,
)
from core.orchestrator import session_history
from core.health_check import run_startup_checks
from core.config_loader import config_loader_module
from core.event_bus import event_bus_module
from core.permissions import permissions_module
from core.backup_manager import backup_manager_module
from core.file_editor import file_editor_module
from core.executor import executor_module
from core.web_search import web_search_module
from core.avatar_router import avatar_router_module
from core.monitor import create_monitor
from core.debug_overlay import DebugOverlay
from pathlib import Path
from core.config_loader import is_read_allowed, CFG
from core.executor import execute_command
from core.backup_manager import restore_latest_backup
from core.event_bus import bus
from core.degradation import on_websocket_degraded, on_websocket_connected
from core.web_search import search, format_for_llm
from core.file_editor import safe_write
from core.tool_registry import registry, Tool

monitor = None  # set in main(), read in cli_input_loop() for cleanup
overlay = None  # set in main(), read in cli_input_loop() for cleanup

# ── Module lifecycle (4s contract, A4) ────────────────────────────────────────
# Every PocketModule starts here, in dependency order, and stops in reverse.
# This is the ONLY place modules start: no hand-wired .start() calls or worker
# threads elsewhere (that was the tts_worker double-start hazard).
LIFECYCLE = [
    logger_module,          # first: everything below logs
    config_loader_module,
    event_bus_module,
    permissions_module,     # ensures logs/ for the decision log
    backup_manager_module,  # ensures the backup dir
    file_editor_module,
    executor_module,
    web_search_module,
    memory_module,          # bootstrap_knowledge()
    stt_module,             # init_whisper()
    websocket_module,       # avatar connection thread
    avatar_router_module,
    tts_module,             # tts-worker thread (the one and only)
    llm_module,             # lazy Ollama client; health_check pings it
]
_started = []  # modules whose start() ran, in order — stopped in reverse

# ── Event wiring (4.5g) ───────────────────────────────────────────────────────
# The ONE place bus subscriptions are made. Producers emit; they never import
# the consumer. Within one event type, handlers run in the order listed here.
EVENT_WIRING = [
    # Conversation + degradation output (orchestrator / degradation.notify)
    ("websocket.send",     websocket_module.on_event),
    ("avatar_router.send", avatar_router_module.on_event),
    ("tts.speak",          tts_module.on_event),
    # Reserved, NOT wired until something emits them (no unused entry points):
    #   "web.search" → web_search_module (5b) · "llm.query" → llm_module
    #   "memory.store" → memory_module
    # WebSocket connection lifecycle (4n) → logging (4i) + degradation (4k)
    ("connection.websocket.connected",    logger_module.on_event),
    ("connection.websocket.disconnected", logger_module.on_event),
    ("connection.websocket.reconnecting", logger_module.on_event),
    ("connection.websocket.degraded",     logger_module.on_event),
    ("connection.websocket.degraded",     on_websocket_degraded),
    ("connection.websocket.connected",    on_websocket_connected),
]


def wire_events():
    for event_type, handler in EVENT_WIRING:
        bus.subscribe(event_type, handler)

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
# Shutdown
# ═════════════════════════════════════════════════════════════════════════════

def _shutdown():
    """Single shutdown path — used by /quit and by Ctrl-C / EOF in the loop."""
    if overlay:
        overlay.stop()
    if monitor:
        monitor.stop()
    log.info("pocket", "Pocket signing off")
    for module in reversed(_started):  # logger stops last
        try:
            module.stop()
        except Exception as e:  # stop() must never raise (4s); don't let one block exit
            print(f"  [{type(module).__name__}.stop() error: {e}]")
    print(f"\n  [Pocket signing off. Later{' ' + CFG['user_name'] if CFG['user_name'] else ''}.]\n")
    os._exit(0)


# ═════════════════════════════════════════════════════════════════════════════
# Tool handlers — each takes the raw argument string (guaranteed non-empty for
# takes_args tools; the registry prints usage before calling otherwise).
# ═════════════════════════════════════════════════════════════════════════════

def _tool_quit(args):
    _shutdown()


def _tool_clear(args):
    session_history.clear()
    print("  [Session cleared]\n")


def _tool_memory(args):
    print(f"  [Memory: {memory.count()} entries in ChromaDB]\n")


def _tool_load(args):
    load_knowledge_file(args)


# Formats /read can't handle as plain text (need parsing, not decoding)
_BINARY_SUFFIXES = {".docx", ".doc", ".pdf", ".xlsx", ".xls",
                    ".pptx", ".ppt", ".zip", ".png", ".jpg", ".jpeg", ".gif"}


def _load_text_file(filepath):
    """Shared by /read and the model's read tool (4.5f NL dispatch).

    Returns (content, path, error). On success error is None; on failure
    content is None and error is the message to show.
    """
    path = (
        Path(filepath)
        if Path(filepath).is_absolute()
        else Path(project_root) / filepath
    )

    if not is_read_allowed(str(path)):
        return None, path, f"/read blocked: {filepath} is on the denylist"

    try:
        if path.suffix.lower() in _BINARY_SUFFIXES:
            return None, path, (f"/read: {path.suffix} is a binary/office format — "
                                f"/read handles plain text only for now.")

        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            content = path.read_text(encoding="cp1252")  # Windows-saved text fallback

        return content, path, None

    except FileNotFoundError:
        return None, path, f"File not found: {path}"

    except Exception as e:
        return None, path, f"/read error: {e}"


def _tool_read(args):
    filepath = args
    content, path, error = _load_text_file(filepath)

    if error:
        print(f"  [{error}]\n")
        return

    print(f"  [Loaded: {path} ({len(content)} chars)]\n")

    handle_user_input_sync(
        f"I'm showing you this file: {filepath}\n\n```\n{content}\n```",
        persist=False,
    )


def _tool_edit(args):
    filepath = args

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
        return

    result = safe_write(filepath, "\n".join(lines))
    print(f"  {result}\n")


def _tool_search(args):
    query = args

    print(f"  [Searching the web for: {query}]\n")

    # The user typed this themselves — their invocation is the approval.
    result = search(query, require_approval=False)

    if not result["ok"]:
        print(f"  [/search failed: {result['error']}]\n")
        return

    handle_user_input_sync(
        f"I searched the web for: {query}\n\n"
        f"Here are the results:\n\n{format_for_llm(result)}",
        persist=False,
    )


def _tool_exec(args):
    command = args

    print(f"  [Executing: {command}]\n")

    result = execute_command(command)

    print(result)
    print()


def _tool_rollback(args):
    filepath = args

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


# ═════════════════════════════════════════════════════════════════════════════
# Model-path handlers (4.5f NL dispatch) — take the schema-validated args dict
# and RETURN text for the model. They run inside the current turn, after
# propose_action() approved the call, so they must never start a new turn
# (handle_user_input_sync would deadlock on the turn mutex).
# ═════════════════════════════════════════════════════════════════════════════

def _model_memory(args):
    return f"Memory holds {memory.count()} entries in ChromaDB."


def _model_read(args):
    filepath = args["filepath"]
    content, path, error = _load_text_file(filepath)
    if error:
        return f"Could not read the file. {error}"
    print(f"  [Loaded: {path} ({len(content)} chars)]\n")
    return f"Contents of {filepath}:\n\n```\n{content}\n```"


def _model_search(args):
    query = args["query"]
    print(f"  [Searching the web for: {query}]\n")
    # Approval already happened in propose_action() (ADR-001); don't ask twice.
    result = search(query, require_approval=False)
    if not result["ok"]:
        return f"Web search failed: {result['error']}"
    return format_for_llm(result)


# ═════════════════════════════════════════════════════════════════════════════
# Tool registry — schema-first. Typed slash commands use `handler` (typing it is
# the approval). Model-callable tools also carry a `model_handler`; the model's
# calls are validated against params_schema and ALL go through propose_action()
# (core/nl_dispatch.py, ADR-001).
# ═════════════════════════════════════════════════════════════════════════════

registry.register(Tool(
    name="/quit",
    handler=_tool_quit,
    description="Shut Pocket down cleanly.",
    aliases=("quit", "exit", "bye"),
    exact=True,  # bare-word aliases must be the whole line, not just the first token
    risk="low",
    params_schema={"type": "object", "properties": {}},
))

registry.register(Tool(
    name="/clear",
    handler=_tool_clear,
    description="Clear the in-session conversation history.",
    risk="low",
    params_schema={"type": "object", "properties": {}},
))

registry.register(Tool(
    name="/memory",
    handler=_tool_memory,
    description="Report how many entries are stored in ChromaDB.",
    risk="low",
    model_callable=True,  # 4.5f NL dispatch: exposed to the model, still gated
    model_handler=_model_memory,
    params_schema={"type": "object", "properties": {}, "additionalProperties": False},
))

registry.register(Tool(
    name="/load",
    handler=_tool_load,
    description="Load a knowledge file into memory.",
    takes_args=True,
    arg_hint="<file>",
    usage="[/load requires a filepath]",
    risk="low",
    params_schema={
        "type": "object",
        "properties": {"filepath": {"type": "string", "description": "Knowledge file to load"}},
        "required": ["filepath"],
    },
))

registry.register(Tool(
    name="/read",
    handler=_tool_read,
    description="Read a plain-text file and show its contents to Pocket (not persisted).",
    takes_args=True,
    arg_hint="<file>",
    usage="[/read requires a filepath]",
    risk="low",
    model_callable=True,  # 4.5f NL dispatch: exposed to the model, still gated
    model_handler=_model_read,
    params_schema={
        "type": "object",
        "properties": {"filepath": {"type": "string", "minLength": 1, "description": "Text file to read"}},
        "required": ["filepath"],
        "additionalProperties": False,
    },
))

registry.register(Tool(
    name="/edit",
    handler=_tool_edit,
    description="Overwrite a file with pasted content (backup-before-write via safe_write).",
    takes_args=True,
    arg_hint="<file>",
    usage="[/edit requires a filepath]",
    risk="high",
    params_schema={
        "type": "object",
        "properties": {"filepath": {"type": "string", "description": "File to overwrite"}},
        "required": ["filepath"],
    },
))

registry.register(Tool(
    name="/search",
    handler=_tool_search,
    description="Search the web (Tavily) and hand the results to Pocket (not persisted).",
    takes_args=True,
    arg_hint="<query>",
    usage="[/search requires a query]",
    risk="low",
    model_callable=True,  # 4.5f NL dispatch: exposed to the model, still gated
    model_handler=_model_search,
    params_schema={
        "type": "object",
        "properties": {"query": {"type": "string", "minLength": 1, "description": "Web search query"}},
        "required": ["query"],
        "additionalProperties": False,
    },
))

registry.register(Tool(
    name="/exec",
    handler=_tool_exec,
    description="Run a command through the constrained executor (approval-gated).",
    takes_args=True,
    arg_hint="<command>",
    usage="[/exec requires a command]",
    risk="high",
    params_schema={
        "type": "object",
        "properties": {"command": {"type": "string", "description": "Command line to execute"}},
        "required": ["command"],
    },
))

registry.register(Tool(
    name="/rollback",
    handler=_tool_rollback,
    description="Restore a file from its most recent backup.",
    takes_args=True,
    arg_hint="<file>",
    usage="[/rollback requires a filepath]",
    risk="medium",
    params_schema={
        "type": "object",
        "properties": {"filepath": {"type": "string", "description": "File to restore"}},
        "required": ["filepath"],
    },
))


# ═════════════════════════════════════════════════════════════════════════════
# CLI — text input loop
# ═════════════════════════════════════════════════════════════════════════════

def cli_input_loop():
    print("\nType a message or hold F9 to speak.")
    print(registry.format_commands() + "\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            _shutdown()

        if not user_input:
            continue

        if registry.dispatch(user_input):
            continue

        handle_user_input_sync(user_input, allow_tools=True)

# ═════════════════════════════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════════════════════════════

def main():
    greeting = f"Pocket is online. Hey {CFG['user_name'] or 'there'}."
    width = max(34, len(greeting) + 6)
    print(f"\n╔{'═' * width}╗")
    print(f"║{greeting.center(width)}║")
    print(f"╚{'═' * width}╝\n")

    wire_events()  # before any module starts, so startup-time events aren't dropped

    for module in LIFECYCLE:
        module.start()
        _started.append(module)
        if module is logger_module:
            log.info("pocket", "Pocket starting up")

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
    if not run_startup_checks(modules, send_dict_to_avatar):
        sys.exit(1)

    # Continuous self-monitoring (Stage 4j.1)
    global monitor
    monitor = create_monitor(modules)
    monitor.start()

    # Runtime debug overlay (Stage 4t)
    global overlay
    overlay = DebugOverlay(send_to_avatar_fn=send_dict_to_avatar)

    # Alt+D hotkey thread
    altd_thread = threading.Thread(target=altd_listener, daemon=True)
    altd_thread.start()

    # CLI runs on main thread
    cli_input_loop()


if __name__ == "__main__":
    main()