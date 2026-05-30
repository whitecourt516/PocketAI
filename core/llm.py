# core/llm.py
# Ollama LLM — session history, memory integration, avatar routing.
#
# Public API:
#   session_history              — list of chat turns (mutable, shared state)
#   handle_user_input_sync(text) — process input, get reply, update everything
#
# Stage 4s: LLMModule implements PocketModule.
#   start()        — no-op; Ollama client is lazy (connects on first call)
#   stop()         — clears session_history so memory is clean on next run
#   health_check() — sends a minimal ping to Ollama and checks for a response
#   on_event()     — handles "llm.query" events from the bus (4q)

import os

import ollama

from config.settings import MODEL
from persona.prompt_loader import SYSTEM_PROMPT
from core.memory import get_relevant_memories, save_memory
from core.websocket_server import websocket_module
from core.tts import tts_queue
from core.pocket_module import PocketModule
from core.degradation import mark_degraded, mark_recovered


# ── Ollama client ─────────────────────────────────────────────────────────────
ollama_client = ollama.Client(host=os.getenv("OLLAMA_HOST", "http://localhost:11434"))

# ── Session state ─────────────────────────────────────────────────────────────
session_history = []


# ═════════════════════════════════════════════════════════════════════════════
# CORE FUNCTIONS (unchanged public API)
# ═════════════════════════════════════════════════════════════════════════════

def handle_user_input_sync(text: str):
    """Process user input, get LLM reply, update memory and avatar."""
    global session_history

    websocket_module.send({"type": "expression", "value": "thinking"})
    websocket_module.send({"type": "wander_pause"})

    past        = get_relevant_memories(text)
    full_system = SYSTEM_PROMPT + (f"\n\n{past}" if past else "")

    messages = [{"role": "system", "content": full_system}]
    messages += session_history
    messages.append({"role": "user", "content": text})

    try:
        response = ollama_client.chat(model=MODEL, messages=messages)
        reply    = response["message"]["content"]
    except Exception as e:
        # Ollama unreachable / errored — degrade gracefully instead of dying.
        # mark_degraded handles the flag, log, event, and the spoken message.
        mark_degraded("ollama", str(e))
        websocket_module.send({"type": "wander_resume"})
        return

    mark_recovered("ollama")  # no-op unless Ollama had been down

    session_history.append({"role": "user",      "content": text})
    session_history.append({"role": "assistant",  "content": reply})

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
            response = ollama_client.chat(
                model=MODEL,
                messages=[{"role": "user", "content": "hi"}],
                options={"num_predict": 1},
            )
            return bool(response.get("message", {}).get("content"))
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
