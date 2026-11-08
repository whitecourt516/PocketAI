# core/orchestrator.py
# Conversation orchestrator — the turn pipeline.
#
# Owns:
#   session_history          — list of chat turns (mutable, shared state)
#   run_turn(text, persist, prefetched=None, allow_tools=False)
#                            — the full turn pipeline
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
#
# 4.5g: output goes out over the event bus, never by direct import. The turn
# emits "websocket.send" / "avatar_router.send" / "tts.speak"; pocket.py's
# EVENT_WIRING routes them to each module's on_event(). Delivery order is the
# emit order below (expression → avatar text → voice), and bus.emit is
# synchronous, so ordering is the same as the old direct calls.

from persona.prompt_loader import build_system_prompt
from core.memory import get_relevant_memories, save_memory
from core.event_bus import bus
from core.degradation import mark_degraded, mark_recovered
from core.ollama_client import chat
from core.nl_dispatch import TOOL_GUIDANCE, run_with_tools


# ── Session state ─────────────────────────────────────────────────────────────
session_history = []

# ── Prompt-assembly seam ──────────────────────────────────────────────────────
# retrieved chunks → [compression] → context injection.
# Passthrough until 6g wires the LLMLingua-style compressor (token-level strip of
# retrieved memory before injection; complements 6g's content-level summarisation).
# Leaving the seam here now means 6g drops the compressor into one place instead
# of retrofitting it into a finished assembly line. (impr. #5)
def compress_context(chunks: str) -> str:
    return chunks

def run_turn(
    text: str,
    persist: bool = True,
    prefetched: str | None = None,
    allow_tools: bool = False,
) -> None:
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
    prefetched    — retrieved memory computed *outside* the lock (Stage 5 STT
                    prefetch). None → not provided → retrieve inline (the only
                    path today). Either way the result is consumed here, under
                    the mutex, so retrieval-through-write stays serialized.
    allow_tools   — offer model-callable tools (4.5f NL dispatch, ADR-001).
                    Any tool call the model makes is schema-validated and
                    routed through propose_action() in core.nl_dispatch. A turn
                    where a tool ran is treated as persist=False, like /read.
    """
    global session_history

    bus.emit("websocket.send", {"data": {"type": "expression", "value": "thinking"}})
    bus.emit("websocket.send", {"data": {"type": "wander_pause"}})

    # CHANGED: retrieval is injectable — prefetch feeds in, else retrieve inline.
    past        = prefetched if prefetched is not None else get_relevant_memories(text)
    past        = compress_context(past)  # CHANGED: passthrough seam (impr. #5)
    full_system = build_system_prompt() + (f"\n\n{past}" if past else "")
    if allow_tools:
        full_system += f"\n\n{TOOL_GUIDANCE}"

    messages = [{"role": "system", "content": full_system}]
    messages += session_history
    messages.append({"role": "user", "content": text})

    tool_messages = []  # assistant tool_call + tool result pairs from this turn
    try:
        if allow_tools:
            reply, tool_messages, tool_ran = run_with_tools(messages)
            if tool_ran:
                persist = False  # tool output (file/web) stays out of vector memory
        else:
            reply = chat(messages)
    except Exception as e:
        # Ollama unreachable / errored — degrade gracefully instead of dying.
        mark_degraded("ollama", str(e))
        bus.emit("websocket.send", {"data": {"type": "wander_resume"}})
        return

    mark_recovered("ollama")  # no-op unless Ollama had been down

    # Injected content joins session_history regardless of persist, so the
    # next turn can still reference the file/search results in-session.
    session_history.append({"role": "user",      "content": text})
    session_history.extend(tool_messages)  # keeps tool results for follow-ups
    session_history.append({"role": "assistant",  "content": reply})

    # ...but only normal turns are committed to permanent vector memory.
    if persist:
        save_memory("user",      text)
        save_memory("assistant", reply)

    print(f"\nPocket: {reply}\n")

    bus.emit("avatar_router.send", {"text": reply})  # expression + subtitle + panel
    bus.emit("tts.speak",          {"text": reply})  # then voice