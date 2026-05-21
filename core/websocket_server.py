# core/websocket_server.py
# Avatar WebSocket connection — connects to Electron and sends messages.
#
# Public API:
#   start_avatar_connection()          — call once at startup
#   avatar_send(msg)                   — thread-safe fire-and-forget
#   avatar_expression(name)            — send an expression
#   avatar_subtitle(text, duration)    — send subtitle text
#   avatar_panel(content, type, title) — open output panel
#   avatar_panel_close()               — close output panel
#   avatar_thinking()                  — expression + pause wander
#   avatar_done_thinking()             — resume wander
#
# Stage 4s: WebSocketModule implements PocketModule.
#   start()        — calls start_avatar_connection()
#   stop()         — stops the asyncio event loop cleanly
#   health_check() — returns _avatar_connected
#   on_event()     — handles "avatar.*" events from the bus (4q)

import asyncio
import json
import threading
import time

import websockets

from core.config_loader import CFG
from core.pocket_module import PocketModule

AVATAR_WS_URL = CFG["avatar"]["websocket_url"]

# ── Runtime state ─────────────────────────────────────────────────────────────
_avatar_ws        = None
_avatar_connected = False
_loop             = None
_loop_thread: threading.Thread | None = None


# ═════════════════════════════════════════════════════════════════════════════
# INTERNAL — async connect + send
# ═════════════════════════════════════════════════════════════════════════════

async def _avatar_connect():
    global _avatar_ws, _avatar_connected
    try:
        _avatar_ws = await websockets.connect(AVATAR_WS_URL)
        _avatar_connected = True
        print("  [Avatar connected ✓]")
    except Exception:
        _avatar_connected = False


async def _avatar_send(msg: dict):
    global _avatar_ws, _avatar_connected
    if not _avatar_connected or not _avatar_ws:
        return
    try:
        await _avatar_ws.send(json.dumps(msg))
    except Exception:
        _avatar_connected = False


async def _avatar_disconnect():
    global _avatar_ws, _avatar_connected
    if _avatar_ws:
        try:
            await _avatar_ws.close()
        except Exception:
            pass
    _avatar_connected = False
    _avatar_ws = None


def _run_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()


# ═════════════════════════════════════════════════════════════════════════════
# PUBLIC API (unchanged)
# ═════════════════════════════════════════════════════════════════════════════

def start_avatar_connection():
    """Spin up the async event loop and connect to the Electron avatar."""
    global _loop, _loop_thread
    _loop = asyncio.new_event_loop()
    _loop_thread = threading.Thread(target=_run_loop, args=(_loop,), daemon=True, name="ws-loop")
    _loop_thread.start()
    time.sleep(0.5)
    asyncio.run_coroutine_threadsafe(_avatar_connect(), _loop)


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


# ═════════════════════════════════════════════════════════════════════════════
# LIFECYCLE — Stage 4s
# ═════════════════════════════════════════════════════════════════════════════

class WebSocketModule(PocketModule):
    """Lifecycle wrapper for the avatar WebSocket connection.

    start()        — starts the asyncio loop thread and connects to Electron.
    stop()         — closes the WebSocket and stops the event loop.
    health_check() — returns True if the connection is currently established.
    on_event()     — handles "avatar.*" bus events and dispatches to the avatar.
                     This is the main path 4q will use to send avatar commands
                     without any module importing websocket_server directly.
    """

    def start(self) -> None:
        start_avatar_connection()

    def stop(self) -> None:
        if _loop and _loop.is_running():
            asyncio.run_coroutine_threadsafe(_avatar_disconnect(), _loop)
            time.sleep(0.3)
            _loop.call_soon_threadsafe(_loop.stop)

    def health_check(self) -> bool:
        try:
            return _avatar_connected
        except Exception as e:
            print(f"  [WebSocketModule] health_check error: {e}")
            return False

    def on_event(self, event: dict) -> None:
        # Dispatch avatar.* bus events to the appropriate send function.
        # {"type": "avatar.expression", "name": "happy"}
        # {"type": "avatar.subtitle",   "text": "...", "duration": 4000}
        # {"type": "avatar.panel",      "content": "...", "content_type": "text", "title": "Pocket"}
        # {"type": "avatar.panel_close"}
        # {"type": "avatar.thinking"}
        # {"type": "avatar.done_thinking"}
        t = event.get("type", "")
        if t == "avatar.expression":
            avatar_expression(event.get("name", "neutral"))
        elif t == "avatar.subtitle":
            avatar_subtitle(event.get("text", ""), event.get("duration", 5000))
        elif t == "avatar.panel":
            avatar_panel(
                event.get("content", ""),
                event.get("content_type", "text"),
                event.get("title", "Pocket"),
            )
        elif t == "avatar.panel_close":
            avatar_panel_close()
        elif t == "avatar.thinking":
            avatar_thinking()
        elif t == "avatar.done_thinking":
            avatar_done_thinking()


websocket_module = WebSocketModule()
