# core/orchestrator.py
# Conversation orchestrator — the turn pipeline.
#
# Owns:
#   session_history          — list of chat turns (mutable, shared state)
#   run_turn(text, persist)  — the full turn pipeline
#
# This is the seam every Stage 6 feature plugs into. The pipeline runs under
# the turn mutex held by core.llm.TurnManager — run_turn itself does no
# locking; TurnManager.run wraps it. Keeping run_turn lock-free here means a
# future consolidation pass holding turn_manager.exclusive() serializes
# against the *same* lock without orchestrator needing to know about it.
#
# 4.5f: extracted from llm.py's _run_turn. Transport (ollama_client) sits
# below this; the mutex (TurnManager) sits above. Memory / degradation /
# dispatch policy lives here.

from persona.prompt_loader import build_system_prompt
from core.memory import get_relevant_memories, save_memory
from core.websocket_server import websocket_module
from core.tts import tts_queue
from core.degradation import mark_degraded, mark_recovered
from core.ollama_client import chat


# ── Session state ─────────────────────────────────────────────────────────────
session_history = []


def run_turn(text: str, persist: bool = True) -> None:
    """The turn pipeline. Runs under the turn mutex (see core.llm.TurnManager).

    Everything from memory retrieval through memory write and dispatch lives
    here so no two turns can interleave on session_history, and so a future
    consolidation pass holding turn_manager.exclusive() can't slip between
    retrieval and write.

    persist=True  — normal conversation; user + reply written to ChromaDB.
    persist=False — context-injection turn (/read, /search): the content and
                    reply join session_history so follow-ups work, but neither
                    is written to permanent vector memory. Stops file dumps /
                    web results from polluting semantic search. This is the seam
                    5e flips to tagged-ephemeral storage once a consumer exists.
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