# core/llm.py
# Ollama LLM — session history, memory integration, avatar routing.
#
# Public API:
#   session_history          — list of chat turns (mutable, shared state)
#   handle_user_input_sync(text) — process input, get reply, update everything

import os

import ollama

from config.settings import MODEL
from persona.prompt_loader import SYSTEM_PROMPT
from core.memory import get_relevant_memories, save_memory
from core.websocket_server import avatar_thinking, avatar_done_thinking
from core.tts import tts_queue

# ── Ollama client ─────────────────────────────────────────────────────────────
ollama_client = ollama.Client(host=os.getenv("OLLAMA_HOST", "http://localhost:11434"))

# ── Session state ─────────────────────────────────────────────────────────────
session_history = []


# ═════════════════════════════════════════════════════════════════════════════
# LLM
# ═════════════════════════════════════════════════════════════════════════════

def handle_user_input_sync(text: str):
    """Process user input, get LLM reply, update memory and avatar.

    Imports send_to_avatar locally to avoid a circular import
    (send_to_avatar lives in pocket.py and calls back into core modules).
    """
    global session_history

    avatar_thinking()

    past        = get_relevant_memories(text)
    full_system = SYSTEM_PROMPT + (f"\n\n{past}" if past else "")

    messages = [{"role": "system", "content": full_system}]
    messages += session_history
    messages.append({"role": "user", "content": text})

    try:
        response = ollama_client.chat(model=MODEL, messages=messages)
        reply    = response["message"]["content"]
    except Exception as e:
        reply = f"[LLM error: {e}]"
        print(reply)
        avatar_done_thinking()
        return

    session_history.append({"role": "user",      "content": text})
    session_history.append({"role": "assistant",  "content": reply})

    save_memory("user",      text)
    save_memory("assistant", reply)

    print(f"\nPocket: {reply}\n")

    # Local import breaks the circular dependency:
    # pocket.py → core.llm → (would circle back via send_to_avatar)
    from pocket import send_to_avatar
    send_to_avatar(reply)

    tts_queue.put(reply)
