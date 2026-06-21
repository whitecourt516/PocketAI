# core/websocket_server.py
# Stage 4n — WebSocket Reconnection Engine (built on top of 4r state manager)
#
# Manages the persistent WebSocket connection between pocket.py and the
# Electron avatar. Detects disconnects, retries with exponential backoff
# (cap: 60s, max: 10 attempts), re-syncs avatar state on reconnect.
#
# Backoff schedule (seconds): 1, 2, 4, 8, 16, 30, 60, 60, 60, 60 → DEGRADED_MODE
# A10: DEGRADED_MODE is non-terminal — slow-polls every 60s and recovers.
#
# State machine (lives in state_manager, namespace "connection"):
#   CONNECTED → DISCONNECTED → RECONNECTING → RESYNCING → CONNECTED
#                                           ↓ (10 failures)
#                                        DEGRADED_MODE → (slow-poll) → CONNECTED
#
# Stage 4s: WebSocketModule implements PocketModule.

import asyncio
import json
import threading
import time
import traceback

import websockets
import websockets.connection

from core.pocket_module import PocketModule
from core.state_manager import state
from core.event_bus import bus
from core.config_loader import CFG
from core.logger import log


# ═════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ═════════════════════════════════════════════════════════════════════════════

BACKOFF_SCHEDULE = [1, 2, 4, 8, 16, 30, 60, 60, 60, 60]  # seconds, 10 attempts
MAX_ATTEMPTS     = len(BACKOFF_SCHEDULE)
DEGRADED_RETRY_INTERVAL = 60  # seconds — slow-poll cadence once aggressive backoff is exhausted (A10)


# ═════════════════════════════════════════════════════════════════════════════
# WEBSOCKET MODULE
# ═════════════════════════════════════════════════════════════════════════════

class WebSocketModule(PocketModule):
    """
    Manages the WebSocket connection to the Electron avatar.
    Runs a background thread that owns the asyncio event loop.
    All public methods (send, start, stop) are thread-safe.
    """

    def __init__(self):
        self._ws           = None          # live websocket connection
        self._loop         = None          # asyncio loop owned by background thread
        self._thread       = None          # background thread
        self._running      = False         # set False to trigger clean shutdown
        self._lock         = threading.Lock()

    # ------------------------------------------------------------------
    # PocketModule interface
    # ------------------------------------------------------------------

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return  # already running

        self._running = True
        self._thread  = threading.Thread(
            target=self._run_loop,
            name="websocket-manager",
            daemon=True
        )
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._loop and self._loop.is_running():
            asyncio.run_coroutine_threadsafe(self._disconnect(), self._loop)
        if self._thread:
            self._thread.join(timeout=5)
        state.set_websocket_status("DISCONNECTED")

    def health_check(self) -> bool:
        return state.websocket_status == "CONNECTED"

    def on_event(self, event: dict) -> None:
        # Supported: {"type": "websocket.send", "data": {...}}
        if event.get("type") != "websocket.send":
            return
        data = event.get("data")
        if data:
            self.send(data)

    # ------------------------------------------------------------------
    # Public send — callable from any thread
    # ------------------------------------------------------------------

    def send(self, data: dict) -> bool:
        """
        Send a dict to the avatar as JSON.
        Returns True if sent, False if not connected.
        Silently drops the message in DEGRADED_MODE — Pocket keeps running.
        """
        if state.websocket_status not in ("CONNECTED", "RESYNCING"):
            return False
        if not self._loop or not self._loop.is_running():
            return False

        future = asyncio.run_coroutine_threadsafe(
            self._send_raw(json.dumps(data)),
            self._loop
        )
        try:
            future.result(timeout=3)
            return True
        except Exception as e:
            print(f"  [WebSocket] send failed: {e}")
            log.error("websocket", f"send failed: {e}")
            return False

    # ------------------------------------------------------------------
    # Background thread — owns the asyncio loop
    # ------------------------------------------------------------------

    def _run_loop(self) -> None:
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._connection_manager())
        finally:
            self._loop.close()

    # ------------------------------------------------------------------
    # Connection manager — reconnect loop
    # ------------------------------------------------------------------

    async def _connection_manager(self) -> None:
        url = CFG.get("avatar", {}).get("websocket_url", "ws://localhost:7845")

        while self._running:
            attempt  = state.get("connection", "reconnect_attempts")
            degraded = attempt >= MAX_ATTEMPTS

            if degraded:
                # Aggressive backoff exhausted. Switch to a slow poll, but KEEP
                # trying — a relaunched avatar (4.5b) should reconnect on its own
                # without a Pocket restart. (A10: DEGRADED_MODE is no longer terminal.)
                if state.websocket_status != "DEGRADED_MODE":
                    state.set_websocket_status("DEGRADED_MODE")
                    bus.emit("connection.websocket.degraded", {
                        "reason": "Max aggressive attempts reached; slow-polling",
                        "attempts": attempt,
                    })
                    print(f"  [WebSocket] DEGRADED_MODE after {attempt} attempts — "
                          f"slow-polling every {DEGRADED_RETRY_INTERVAL}s until the avatar returns.")
            elif attempt > 0:
                state.set_websocket_status("RECONNECTING")
                bus.emit("connection.websocket.reconnecting", {"attempt": attempt})

            try:
                async with websockets.connect(url, open_timeout=5) as ws:
                    with self._lock:
                        self._ws = ws

                    # set_websocket_status("CONNECTED") resets reconnect_attempts to 0,
                    # so recovery is durable — including recovery straight out of
                    # DEGRADED_MODE. Next drop starts the backoff schedule fresh.
                    state.set_websocket_status("CONNECTED")
                    bus.emit("connection.websocket.connected", {"attempt": attempt})

                    if attempt > 0:
                        # Reconnect (or degraded-recovery) — re-sync avatar state.
                        await self._resync()

                    print(f"  [WebSocket] Connected to avatar at {url}")

                    # Hold connection open, detect drops
                    await self._hold(ws)

            except Exception as e:
                with self._lock:
                    self._ws = None

                attempts_now = state.increment_reconnect_attempts()

                # Past the cap, stay in DEGRADED_MODE rather than flapping to
                # DISCONNECTED — the status should read "slow-polling," not churn.
                if attempts_now < MAX_ATTEMPTS:
                    state.set_websocket_status("DISCONNECTED")
                else:
                    state.set_websocket_status("DEGRADED_MODE")

                bus.emit("connection.websocket.disconnected", {
                    "reason": str(e),
                    "attempt": attempts_now,
                })

                # Guard the backoff index — attempts_now climbs past MAX_ATTEMPTS
                # during slow-poll, so only index the schedule while in range.
                if attempts_now < MAX_ATTEMPTS:
                    wait = BACKOFF_SCHEDULE[attempts_now - 1]
                    print(f"  [WebSocket] Disconnected ({e}). Retry {attempts_now}/{MAX_ATTEMPTS} in {wait}s...")
                else:
                    wait = DEGRADED_RETRY_INTERVAL
                    print(f"  [WebSocket] Disconnected ({e}). DEGRADED — next slow-poll in {wait}s...")

                await asyncio.sleep(wait)

    async def _hold(self, ws) -> None:
        """Keep connection alive until it drops or we're told to stop."""
        try:
            async for _ in ws:
                pass  # drain any incoming messages (avatar → pocket, future use)
        except Exception:
            pass  # disconnect detected — fall back to connection_manager

    async def _resync(self) -> None:
        """After reconnect, push current avatar state from 4r to the avatar."""
        state.set_websocket_status("RESYNCING")
        try:
            expression = state.expression
            speaking   = state.speaking
            thinking   = state.thinking

            if expression and expression != "neutral":
                await self._send_raw(json.dumps({
                    "command": "set_expression",
                    "expression": expression
                }))

            if thinking:
                await self._send_raw(json.dumps({"command": "thinking_start"}))

            if speaking:
                await self._send_raw(json.dumps({"command": "speaking_start"}))

        except Exception as e:
            print(f"  [WebSocket] Resync failed: {e}")
        finally:
            state.set_websocket_status("CONNECTED")

    async def _send_raw(self, message: str) -> None:
        with self._lock:
            ws = self._ws
        if ws:
            await ws.send(message)

    async def _disconnect(self) -> None:
        with self._lock:
            ws = self._ws
        if ws:
            await ws.close()


# Singleton
websocket_module = WebSocketModule()


# ═════════════════════════════════════════════════════════════════════════════
# LEGACY SEND HELPER
# kept so existing pocket.py calls don't break during migration
# ═════════════════════════════════════════════════════════════════════════════

def send_dict_to_avatar(data: dict) -> bool:
    """Thin wrapper — routes through websocket_module.send().

    Renamed from send_to_avatar (A5) so it no longer collides with
    avatar_router.send_to_avatar, which takes a str and routes a full reply.
    """
    return websocket_module.send(data)