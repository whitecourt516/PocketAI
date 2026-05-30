# core/monitor.py
"""
Stage 4j.1 — Continuous Self-Monitoring

Lightweight background thread that periodically checks each service's health
and writes results into the Runtime State Manager (4r) via update_health().

On state change (healthy → unhealthy or vice versa):
  - Prints a warning to terminal
  - Sends an alert event to the avatar (expression change)

Nothing is done automatically beyond alerting. Pocket reports, user decides.
"""

import threading
import time
import logging
from typing import Optional, Callable

from core.state_manager import state
from core.degradation import mark_degraded, mark_recovered

logger = logging.getLogger(__name__)

# ─── Default thresholds ───────────────────────────────────────────────────────
# Override these in config.yaml under monitoring: if you want tighter/looser checks.

DEFAULT_INTERVAL_SECONDS = 30       # how often the monitor loop runs
OLLAMA_LATENCY_WARN_MS   = 5000     # warn if Ollama response takes longer than this
CHROMA_WARN_SIZE_MB      = 500      # warn if chroma_data grows beyond this


class ServiceMonitor:
    """
    Monitors all registered services in a background daemon thread.
    Writes health booleans into state_manager. Emits avatar alerts on degradation.
    """

    def __init__(
        self,
        modules: dict,
        send_to_avatar_fn: Optional[Callable] = None,
        interval: int = DEFAULT_INTERVAL_SECONDS,
    ):
        """
        Args:
            modules:            dict mapping service key → PocketModule instance
                                Expected keys: "llm", "memory", "tts", "ws"
            send_to_avatar_fn:  callable(command_dict) — sends events to Electron avatar
            interval:           seconds between health checks
        """
        self._modules         = modules
        self._send_to_avatar  = send_to_avatar_fn
        self._interval        = interval
        self._stop_event      = threading.Event()
        self._thread: Optional[threading.Thread] = None

        # Track last known health so we only alert on *changes*
        # None = not yet checked; True = healthy; False = unhealthy
        self._last_known: dict[str, Optional[bool]] = {
            "ollama":    None,
            "chroma":    None,
            "piper":     None,
            "websocket": None,
        }

        # Map module keys → state_manager service names
        # (websocket_server module is keyed "ws" in modules dict but "websocket" in state)
        self._key_map = {
            "llm":    "ollama",
            "memory": "chroma",
            "tts":    "piper",
            "ws":     "websocket",
        }

    # ─── Public interface (PocketModule-compatible) ───────────────────────────

    def start(self) -> None:
        """Start the background monitoring thread."""
        if self._thread and self._thread.is_alive():
            logger.warning("[monitor] Already running — ignoring start() call")
            return

        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._loop,
            name="pocket-monitor",
            daemon=True,   # dies automatically when main process exits
        )
        self._thread.start()
        logger.info(f"[monitor] Started — checking every {self._interval}s")

    def stop(self) -> None:
        """Signal the monitoring thread to stop and wait for it to exit."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("[monitor] Stopped")

    def health_check(self) -> bool:
        """4s contract — the monitor itself is healthy if its thread is alive."""
        return self._thread is not None and self._thread.is_alive()

    def on_event(self, event: dict) -> None:
        """4s contract — monitor doesn't currently respond to bus events."""
        pass

    # ─── Internal loop ────────────────────────────────────────────────────────

    def _loop(self) -> None:
        """Main monitoring loop — runs until stop() is called."""
        # Small initial delay so startup health checks (4j) settle first
        time.sleep(5)

        while not self._stop_event.is_set():
            self._run_checks()
            self._stop_event.wait(timeout=self._interval)

    def _run_checks(self) -> None:
        """Run one round of health checks across all registered modules."""
        for module_key, service_name in self._key_map.items():
            module = self._modules.get(module_key)
            if module is None:
                continue

            try:
                healthy = module.health_check()
            except Exception as exc:
                logger.debug(f"[monitor] health_check() raised for {service_name}: {exc}")
                healthy = False

            # Write into state manager
            state.update_health(service_name, healthy)

            # Alert on state change only
            prev = self._last_known.get(service_name)
            if prev is None:
                # First check — record but don't alert (4j already reported startup state)
                self._last_known[service_name] = healthy
                continue

            if healthy and not prev:
                self._on_recovered(service_name)
            elif not healthy and prev:
                self._on_degraded(service_name)

            self._last_known[service_name] = healthy

    # ─── Alert handlers ───────────────────────────────────────────────────────

    def _on_degraded(self, service_name: str) -> None:
        mark_degraded(service_name)

    def _on_recovered(self, service_name: str) -> None:
        mark_recovered(service_name)


# ─── Convenience factory ──────────────────────────────────────────────────────

def create_monitor(modules: dict, send_to_avatar_fn=None, interval: int = DEFAULT_INTERVAL_SECONDS) -> ServiceMonitor:
    """
    Create and return a ServiceMonitor instance (not yet started).
    Call .start() after Pocket's main loop is ready.

    Usage in pocket.py:
        from core.monitor import create_monitor
        monitor = create_monitor(modules, send_to_avatar_fn=send_to_avatar)
        monitor.start()
    """
    return ServiceMonitor(modules, send_to_avatar_fn, interval)
