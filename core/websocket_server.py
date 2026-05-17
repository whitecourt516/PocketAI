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

import asyncio
import json
import threading
import time

import websockets

AVATAR_WS_URL = "ws://localhost:3000"

# ── Runtime state ─────────────────────────────────────────────────────────────
_avatar_ws        = None
_avatar_connected = False
_loop             = None


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


def _run_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()


# ═════════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ═════════════════════════════════════════════════════════════════════════════

def start_avatar_connection():
    """Spin up the async event loop and connect to the Electron avatar."""
    global _loop
    _loop = asyncio.new_event_loop()
    t = threading.Thread(target=_run_loop, args=(_loop,), daemon=True)
    t.start()
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
