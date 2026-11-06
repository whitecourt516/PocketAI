# core/degradation.py
# Stage 4k — Graceful Degradation
#
# One place for "a service just failed — don't crash, tell the user."
#   notify(message)             — surface a message over every channel that still
#                                 works: terminal always; avatar + voice best-effort,
#                                 each guarded on its own.
#   mark_degraded(service, why) — flip the 4r health flag, log (4i), emit a deduped
#                                 "system.degraded" event (4q), and notify — once.
#   mark_recovered(service)     — the inverse, when a service comes back.
#
# Dedup: a service is announced once. The first detector to call mark_degraded()
# wins; later callers (e.g. the 30s monitor poll after an inline failure) are
# no-ops until it recovers. That's what keeps the inline 4k path and the 4j.1
# monitor from double-reporting the same outage.
#
# Imports: state/bus/log are safe at load time (none import this module).
# websocket_module and tts_queue are imported lazily inside notify() to avoid
# the import cycle (tts -> degradation -> tts) — same trick llm.py already uses
# for avatar_router.

import threading

from core.state_manager import state
from core.event_bus import bus
from core.logger import log

# Names match state_manager's health namespace exactly.
_VALID = {"ollama", "chroma", "piper", "websocket"}

# Per-service user-facing messages. mark_degraded() owns the announcement so the
# dedup guard naturally covers it — no per-turn spam.
_DEGRADED_MSG = {
    "ollama":    "I can't reach my language model right now. I'll keep listening and try again when it's back.",
    "chroma":    "My memory's offline — I'll keep talking, but this turn won't be saved.",
    "piper":     "My voice cut out, so I'll stick to text for now.",
    "websocket": "Lost my avatar connection — still here, reconnecting in the background.",
}
_RECOVERED_MSG = {
    "ollama":    "Language model's back.",
    "chroma":    "Memory's back — saving again.",
    "piper":     "Voice is back.",
    "websocket": "Avatar reconnected.",
}

_degraded: set[str] = set()
_lock = threading.Lock()


def notify(message: str, expression: str = "concerned") -> None:
    """Surface *message* to the user over every channel that still works.

    Terminal always prints. Avatar and voice are best-effort, each guarded on
    its own — if the WebSocket is down, send() just returns False; if Piper is
    the failure, we skip voice entirely so we don't try to speak an "I can't
    speak" message (and so notify can't loop back into a failing TTS worker).
    """
    print(f"\n  [Pocket] {message}\n")

    # Avatar — lazy import breaks the cycle. Uses the {"type","value"} schema
    # the conversational path already uses (not the {"command"} schema).
    try:
        from core.websocket_server import websocket_module
        websocket_module.send({"type": "expression", "value": expression})
        websocket_module.send({"type": "speech", "text": message, "duration": 5000})
    except Exception:
        pass  # avatar is best-effort; never let it bubble

    # Voice — only if Piper isn't the thing that failed. Health is None until
    # checked, so "is not False" means "speak unless we know it's down".
    if state.get("health", "piper") is not False:
        try:
            from core.tts import tts_queue
            tts_queue.put(message)
        except Exception:
            pass


def mark_degraded(service: str, reason: str = "") -> None:
    """Record that *service* failed. No-op if already degraded (dedup)."""
    if service not in _VALID:
        raise ValueError(f"Unknown service: '{service}'")

    with _lock:
        if service in _degraded:
            return  # already announced — stay quiet until it recovers
        _degraded.add(service)

    state.update_health(service, False)   # before notify(), so notify() skips dead TTS
    log.error("degradation", f"{service} degraded: {reason}")
    bus.emit("system.degraded", {"service": service, "reason": reason})
    notify(_DEGRADED_MSG.get(service, f"{service} is unavailable."))


def mark_recovered(service: str) -> None:
    """Record that *service* is healthy again. No-op if it wasn't degraded."""
    if service not in _VALID:
        raise ValueError(f"Unknown service: '{service}'")

    with _lock:
        if service not in _degraded:
            return
        _degraded.discard(service)

    state.update_health(service, True)
    log.info("degradation", f"{service} recovered")
    bus.emit("system.recovered", {"service": service})
    notify(_RECOVERED_MSG.get(service, f"{service} is back."), expression="happy")


def is_degraded(service: str) -> bool:
    with _lock:
        return service in _degraded


# ── WebSocket branch — wired to 4n's existing events (subscribed in pocket.py) ──

def on_websocket_degraded(event: dict) -> None:
    """4n gave up (DEGRADED_MODE). Set avatar neutral in state so resync doesn't
    restore a stale expression, then announce once."""
    state.set_expression("neutral", "degradation")
    mark_degraded("websocket", event.get("reason", ""))


def on_websocket_connected(event: dict) -> None:
    """Fires on every connect; mark_recovered is a no-op unless we were degraded,
    so the first/normal connects stay silent."""
    mark_recovered("websocket")