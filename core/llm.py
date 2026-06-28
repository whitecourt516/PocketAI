# core/llm.py
# LLM facade — turn mutex, public turn API, lifecycle wrapper.
#
# Public API:
#   handle_user_input_sync(text) — process input through the serialized turn
#   turn_manager                 — owns the turn mutex (4.5d)
#   llm_module                   — PocketModule lifecycle wrapper (4s)
#
# The turn pipeline itself lives in core.orchestrator (run_turn); session
# state (session_history) lives there too. This module owns the *mutex* that
# serializes turns and the lifecycle wrapper — not the pipeline body.
#
# 4.5f: _run_turn + session_history extracted to core.orchestrator; raw Ollama
# transport extracted to core.ollama_client. What remains here is the
# concurrency boundary (TurnManager) and the module contract (LLMModule).

import contextlib
import threading

import core.orchestrator as orchestrator
from core.ollama_client import chat
from core.pocket_module import PocketModule


# ═════════════════════════════════════════════════════════════════════════════
# TURN MUTEX — Stage 4.5d
# ═════════════════════════════════════════════════════════════════════════════

class TurnManager:
    """Serializes turns. Owns the turn mutex.

    A 'turn' is the full pipeline — memory retrieval → Ollama call →
    history update → memory write → avatar/TTS dispatch (core.orchestrator.
    run_turn). Only one turn runs at a time, so text, voice, and later
    proactive/idle triggers can't run concurrent turns that race on the
    shared session_history or fire overlapping Ollama calls.

    Blocking acquire: a turn that arrives mid-turn WAITS rather than being
    dropped. (Swap run() to self._lock.acquire(blocking=False) + early
    return if you'd rather drop overlapping input than queue it.)

    exclusive() exposes the same lock to non-turn work that must not race a
    live turn — idle memory consolidation (6h.1) acquires this so a
    background pass can't write mid-turn.
    """

    def __init__(self):
        self._lock = threading.Lock()

    def run(self, text: str, persist: bool = True) -> None:
        with self._lock:
            orchestrator.run_turn(text, persist)

    @contextlib.contextmanager
    def exclusive(self):
        """Acquire the turn mutex directly for non-turn exclusive work
        (e.g. idle consolidation). Blocks until any in-flight turn finishes."""
        with self._lock:
            yield


turn_manager = TurnManager()


# ═════════════════════════════════════════════════════════════════════════════
# PUBLIC TURN API
# ═════════════════════════════════════════════════════════════════════════════

def handle_user_input_sync(text: str, persist: bool = True):
    """Public entry point for a turn. Serialized through the turn mutex.

    persist=True  — normal conversation; written to ChromaDB.
    persist=False — context-injection turn (/read, /search); joins
                    session_history but not permanent vector memory.
    See core.orchestrator.run_turn for the pipeline and the full persist note.
    """
    turn_manager.run(text, persist)


# ═════════════════════════════════════════════════════════════════════════════
# LIFECYCLE — Stage 4s
# ═════════════════════════════════════════════════════════════════════════════

class LLMModule(PocketModule):
    """Lifecycle wrapper for the Ollama LLM.

    start()        — no-op. The Ollama client connects lazily on its first call.
                     If Ollama isn't running, health_check() will catch it.
    stop()         — clears session_history (in place, so imported references
                     stay valid). In-flight requests are not cancelled.
    health_check() — sends a one-token ping ("hi") to Ollama and checks that a
                     non-empty response comes back.
    on_event()     — handles "llm.query" for future bus-driven queries (4q).
    """

    def start(self) -> None:
        # Ollama client is lazy — no connection until first chat() call.
        pass

    def stop(self) -> None:
        # Clear in place — do NOT rebind. orchestrator.session_history is
        # imported by other modules (pocket.py); rebinding the name here would
        # orphan their reference and leave the real list uncleared.
        orchestrator.session_history.clear()

    def health_check(self) -> bool:
        try:
            reply = chat(
                [{"role": "user", "content": "hi"}],
                options={"num_predict": 1},
            )
            return bool(reply)
        except Exception as e:
            print(f"  [LLMModule] health_check error: {e}")
            return False

    def on_event(self, event: dict) -> None:
        # Supported event: {"type": "llm.query", "text": "..."}
        # Reserved for 4q — direct text queries routed through the bus.
        if event.get("type") != "llm.query":
            return
        text = event.get("text", "")
        if text:
            handle_user_input_sync(text)


llm_module = LLMModule()