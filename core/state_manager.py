# core/state_manager.py
"""
Stage 4r — Runtime State Manager
Single source of truth for Pocket's live internal state.
Thread-safe. Read by any module. Written through typed update methods.
"""

import threading
from datetime import datetime
from typing import Any, Optional


class StateManager:
    """
    Central state store for all live runtime values.
    Use the singleton `state` instance — don't instantiate a second one.
    """

    def __init__(self):
        self._lock = threading.RLock()  # Reentrant so modules can read while updating
        self._state = {
            "avatar": {
                "expression": "neutral",
                "speaking": False,
                "thinking": False,
                "expression_source": None,       # which module last set expression
                "expression_set_at": None,        # datetime
            },
            "connection": {
                "websocket": "DISCONNECTED",      # CONNECTED | DISCONNECTED | RECONNECTING | DEGRADED_MODE | RESYNCING
                "last_connected_at": None,        # datetime
                "reconnect_attempts": 0,
            },
            "session": {
                "voice_active": False,
                "current_query": None,
                "skill_mode": "casual",           # casual | coding | cybersecurity | writing | research | planning
                "session_start": datetime.now().isoformat(),
            },
            "health": {
                "ollama": None,                   # True | False | None (unchecked)
                "chroma": None,
                "piper": None,
                "websocket": None,
                "last_checked_at": None,
            },
        }

    # ------------------------------------------------------------------
    # Generic read/write — use typed methods where possible, these for edge cases
    # ------------------------------------------------------------------

    def get(self, namespace: str, key: str, default: Any = None) -> Any:
        with self._lock:
            return self._state.get(namespace, {}).get(key, default)

    def set(self, namespace: str, key: str, value: Any) -> None:
        with self._lock:
            if namespace not in self._state:
                raise KeyError(f"Unknown state namespace: '{namespace}'")
            self._state[namespace][key] = value

    def snapshot(self) -> dict:
        """Return a deep copy of the full state. Safe to read, modifications don't affect live state."""
        import copy
        with self._lock:
            return copy.deepcopy(self._state)

    # ------------------------------------------------------------------
    # Avatar state
    # ------------------------------------------------------------------

    def set_expression(self, expression: str, source: str) -> None:
        with self._lock:
            self._state["avatar"]["expression"] = expression
            self._state["avatar"]["expression_source"] = source
            self._state["avatar"]["expression_set_at"] = datetime.now().isoformat()

    def set_speaking(self, speaking: bool) -> None:
        with self._lock:
            self._state["avatar"]["speaking"] = speaking

    def set_thinking(self, thinking: bool) -> None:
        with self._lock:
            self._state["avatar"]["thinking"] = thinking

    @property
    def expression(self) -> str:
        with self._lock:
            return self._state["avatar"]["expression"]

    @property
    def speaking(self) -> bool:
        with self._lock:
            return self._state["avatar"]["speaking"]

    @property
    def thinking(self) -> bool:
        with self._lock:
            return self._state["avatar"]["thinking"]

    # ------------------------------------------------------------------
    # Connection state
    # ------------------------------------------------------------------

    def set_websocket_status(self, status: str) -> None:
        valid = {"CONNECTED", "DISCONNECTED", "RECONNECTING", "DEGRADED_MODE", "RESYNCING"}
        if status not in valid:
            raise ValueError(f"Invalid websocket status: '{status}'. Must be one of {valid}")
        with self._lock:
            self._state["connection"]["websocket"] = status
            if status == "CONNECTED":
                self._state["connection"]["last_connected_at"] = datetime.now().isoformat()
                self._state["connection"]["reconnect_attempts"] = 0

    def increment_reconnect_attempts(self) -> int:
        with self._lock:
            self._state["connection"]["reconnect_attempts"] += 1
            return self._state["connection"]["reconnect_attempts"]

    @property
    def websocket_status(self) -> str:
        with self._lock:
            return self._state["connection"]["websocket"]

    # ------------------------------------------------------------------
    # Session state
    # ------------------------------------------------------------------

    def set_voice_active(self, active: bool) -> None:
        with self._lock:
            self._state["session"]["voice_active"] = active

    def set_current_query(self, query: Optional[str]) -> None:
        with self._lock:
            self._state["session"]["current_query"] = query

    def set_skill_mode(self, mode: str) -> None:
        valid = {"casual", "coding", "cybersecurity", "writing", "research", "planning"}
        if mode not in valid:
            raise ValueError(f"Invalid skill mode: '{mode}'")
        with self._lock:
            self._state["session"]["skill_mode"] = mode

    @property
    def voice_active(self) -> bool:
        with self._lock:
            return self._state["session"]["voice_active"]

    @property
    def skill_mode(self) -> str:
        with self._lock:
            return self._state["session"]["skill_mode"]

    # ------------------------------------------------------------------
    # Health state — written by 4j.1 monitoring, read by 4t overlay
    # ------------------------------------------------------------------

    def update_health(self, service: str, healthy: bool) -> None:
        valid = {"ollama", "chroma", "piper", "websocket"}
        if service not in valid:
            raise ValueError(f"Unknown service: '{service}'")
        with self._lock:
            self._state["health"][service] = healthy
            self._state["health"]["last_checked_at"] = datetime.now().isoformat()

    def health_summary(self) -> dict:
        with self._lock:
            return dict(self._state["health"])

    def all_healthy(self) -> bool:
        with self._lock:
            checks = [v for k, v in self._state["health"].items() if k != "last_checked_at"]
            return all(v is True for v in checks)

    # ------------------------------------------------------------------
    # Debug repr — used by 4t debug overlay
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        s = self.snapshot()
        av = s["avatar"]
        cn = s["connection"]
        se = s["session"]
        hl = s["health"]

        health_str = " ".join(
            f"{k}={'✅' if v is True else '❌' if v is False else '?'}"
            for k, v in hl.items()
            if k != "last_checked_at"
        )

        return (
            f"[STATE]  expression={av['expression']} | speaking={av['speaking']} | thinking={av['thinking']} | source={av['expression_source']}\n"
            f"[CONN]   websocket={cn['websocket']} | reconnects={cn['reconnect_attempts']}\n"
            f"[SESSION] voice={se['voice_active']} | mode={se['skill_mode']} | query={str(se['current_query'])[:40] if se['current_query'] else None}\n"
            f"[HEALTH] {health_str}"
        )


# Singleton — import this everywhere, don't instantiate StateManager directly
state = StateManager()