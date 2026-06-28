# core/llm.py
# Ollama LLM — session history, memory integration, avatar routing.
#
# Public API:
#   session_history              — list of chat turns (mutable, shared state)
#   handle_user_input_sync(text) — process input, get reply, update everything
#   turn_manager                 — owns the turn mutex (4.5d)
#
# Stage 4s: LLMModule implements PocketModule.
#   start()        — no-op; Ollama client is lazy (connects on first call)
#   stop()         — clears session_history so memory is clean on next run
#   health_check() — sends a minimal ping to Ollama and checks for a response
#   on_event()     — handles "llm.query" events from the bus (4q)

import contextlib
import threading

from persona.prompt_loader import build_system_prompt
from core.memory import get_relevant_memories, save_memory
from core.websocket_server import websocket_module
from core.tts import tts_queue
from core.pocket_module import PocketModule
from core.degradation import mark_degraded, mark_recovered
from core.ollama_client import chat

# ── Session state ─────────────────────────────────────────────────────────────
session_history = []


# ═════════════════════════════════════════════════════════════════════════════
# TURN MUTEX — Stage 4.5d
# ═════════════════════════════════════════════════════════════════════════════

class TurnManager:
    """Serializes turns. Owns the turn mutex.

    A 'turn' is the full pipeline — memory retrieval → Ollama call →
    history update → memory write → avatar/TTS dispatch. Only one turn
    runs at a time, so text, voice, and later proactive/idle triggers
    can't run concurrent turns that race on the unlocked global
    session_history or fire overlapping Ollama calls.

    Blocking acquire: a turn that arrives mid-turn WAITS rather than being
    dropped. (Swap run() to self._lock.acquire(blocking=False) + early
    return if you'd rather drop overlapping input than queue it.)

    exclusive() exposes the same lock to non-turn work that must not race a
    live turn — idle memory consolidation (6h.1) acquires this so a
    background pass can't write mid-turn.

    4.5f: this is the seam the conversation orchestrator extracts into —
    the lock stays here; the turn body moves out of llm.py.
    """

    def __init__(self):
        self._lock = threading.Lock()

    def run(self, text: str, persist: bool = True) -> None:
        with self._lock:
            _run_turn(text, persist)

    @contextlib.contextmanager
    def exclusive(self):
        """Acquire the turn mutex directly for non-turn exclusive work
        (e.g. idle consolidation). Blocks until any in-flight turn finishes."""
        with self._lock:
            yield


turn_manager = TurnManager()


# ═════════════════════════════════════════════════════════════════════════════
# CORE FUNCTIONS (unchanged public API)
# ═════════════════════════════════════════════════════════════════════════════

def handle_user_input_sync(text: str, persist: bool = True):
    """Public API. Serialized through the turn mutex.

    persist=True  — normal conversation; user + reply written to ChromaDB.
    persist=False — context-injection turn (/read, /search): Pocket still
                    sees the content and responds, and it still joins
                    session_history so follow-ups work, but neither the
                    injected blob nor the reply is written to permanent
                    vector memory. Stops file dumps / web results from
                    polluting semantic search. This is the seam 5e flips to
                    tagged-ephemeral storage once a consumer for the tag exists.
    """
    turn_manager.run(text, persist)


def _run_turn(text: str, persist: bool = True):
    """The actual turn pipeline. Runs under the turn mutex (see TurnManager).

    Everything from memory retrieval through memory write and dispatch lives
    here so no two turns can interleave on session_history, and so a future
    consolidation pass holding turn_manager.exclusive() can't slip between
    retrieval and write.
    """
    global session_history

    websocket_module.send({"type": "expression", "value": "thinking"})
    websocket_module.send({"type": "wander_pause"})

    past        = get_relevant_memories(text)
    full_system = build_system_prompt() + (f"\n\n{past}" if past else "")

    messages = [{"role": "system", "content": full_system}]
    messages += session_history
    messages.append({"role": "user", "content": text})

    try:
        reply = chat(messages)
    except Exception as e:
        # Ollama unreachable / errored — degrade gracefully instead of dying.
        mark_degraded("ollama", str(e))
        websocket_module.send({"type": "wander_resume"})
        return

    mark_recovered("ollama")  # no-op unless Ollama had been down

    # Injected content joins session_history regardless of persist, so the
    # next turn can still reference the file/search results in-session.
    session_history.append({"role": "user",      "content": text})
    session_history.append({"role": "assistant",  "content": reply})

    # ...but only normal turns are committed to permanent vector memory.
    if persist:
        save_memory("user",      text)
        save_memory("assistant", reply)

    print(f"\nPocket: {reply}\n")

    from core.avatar_router import send_to_avatar
    send_to_avatar(reply)

    tts_queue.put(reply)


# ═════════════════════════════════════════════════════════════════════════════
# LIFECYCLE — Stage 4s
# ═════════════════════════════════════════════════════════════════════════════

class LLMModule(PocketModule):
    """Lifecycle wrapper for the Ollama LLM.

    start()        — no-op. The Ollama client connects lazily on its first call.
                     If Ollama isn't running, health_check() will catch it.
    stop()         — clears session_history. In-flight requests are not cancelled
                     (Ollama handles its own connection lifecycle).
    health_check() — sends a one-token ping ("hi") to Ollama and checks that
                     a non-empty response comes back. Uses a short timeout so
                     startup health checks don't hang.
    on_event()     — handles "llm.query" for future bus-driven queries (4q).
    """

    def start(self) -> None:
        # Ollama client is lazy — no connection until first .chat() call.
        pass

    def stop(self) -> None:
        global session_history
        session_history = []

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