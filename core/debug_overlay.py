# core/debug_overlay.py
"""
Stage 4t — Runtime Debug Overlay (revised)

Pushes Pocket's live internal state to a dedicated Electron debug panel (debug.html).
Alt+D in Electron toggles the panel. Python side just pushes state on demand or on a
slow polling interval — no terminal reprinting, no rapid firing.

Reads from StateManager (4r) and EventBus (4q).
"""

import threading
import time
import logging
from typing import Optional, Callable

from core.state_manager import state
from core.event_bus import bus
from core.logger import log

LIVE_INTERVAL_SECONDS = 3   # how often to push state in live mode


class DebugOverlay:
    """
    Pushes state snapshots to the Electron debug panel via send_to_avatar_fn.

    Usage:
        overlay = DebugOverlay(send_to_avatar_fn=send_to_avatar)

        # One-shot push (also triggered when panel opens):
        overlay.push()

        # Live mode — pushes every N seconds until stopped:
        overlay.start_live()
        overlay.stop_live()

        # Toggle live on/off (bind to a command or hotkey):
        overlay.toggle_live()
    """

    def __init__(self, send_to_avatar_fn: Optional[Callable] = None):
        self._send            = send_to_avatar_fn
        self._live_thread: Optional[threading.Thread] = None
        self._stop_event      = threading.Event()

    # ─── Public interface ─────────────────────────────────────────────────────

    def push(self) -> None:
        """Push a one-shot state snapshot to the Electron debug panel."""
        payload = self._build_payload()
        self._send_payload(payload)

    def start_live(self, interval: int = LIVE_INTERVAL_SECONDS) -> None:
        """Start pushing state updates every `interval` seconds."""
        if self._live_thread and self._live_thread.is_alive():
            return
        self._stop_event.clear()
        self._live_thread = threading.Thread(
            target=self._live_loop,
            args=(interval,),
            name="pocket-debug-overlay",
            daemon=True,
        )
        self._live_thread.start()
        log.info("overlay", f"Live mode started ({interval}s interval)")

    def stop_live(self) -> None:
        """Stop live push mode."""
        self._stop_event.set()
        if self._live_thread:
            self._live_thread.join(timeout=3)
        log.info("overlay", "Live mode stopped")

    def toggle_live(self, interval: int = LIVE_INTERVAL_SECONDS) -> None:
        """Toggle live mode on/off."""
        if self._live_thread and self._live_thread.is_alive():
            self.stop_live()
        else:
            self.start_live(interval)

    @property
    def live_active(self) -> bool:
        return self._live_thread is not None and self._live_thread.is_alive()

    # ─── PocketModule-compatible stubs ────────────────────────────────────────

    def start(self) -> None:
        pass

    def stop(self) -> None:
        if self.live_active:
            self.stop_live()

    def health_check(self) -> bool:
        try:
            state.snapshot()
            bus.all_event_types()
            return True
        except Exception:
            return False

    def on_event(self, event: dict) -> None:
        pass

    # ─── Internal ─────────────────────────────────────────────────────────────

    def _live_loop(self, interval: int) -> None:
        while not self._stop_event.is_set():
            self.push()
            self._stop_event.wait(timeout=interval)

    def _build_payload(self) -> dict:
        """Build the full state dict to send to the Electron debug panel."""
        snap        = state.snapshot()
        event_types = bus.all_event_types()

        events = []
        for event_type in event_types:
            handlers = bus.subscribers_for(event_type)
            events.append({
                "type":     event_type,
                "handlers": ", ".join(h.__name__ for h in handlers) if handlers else "none",
            })

        return {
            "type": "debug",
            "state": {
                **snap,
                "events": events,
            },
        }

    def _send_payload(self, payload: dict) -> None:
        if self._send is None:
            return
        try:
            self._send(payload)
        except Exception as exc:
            log.error("overlay", f"Send failed: {exc}")
