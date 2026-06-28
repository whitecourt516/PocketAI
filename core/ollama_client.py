# core/ollama_client.py
# Pure Ollama transport. The only place a raw ollama.chat() call lives.
#
# Public API:
#   chat(messages, options=None) -> str
#       Send messages to Ollama, return the reply content as a string.
#       Raises on transport error or malformed response — callers decide
#       policy (degradation, retry, etc.). This module has no opinion on
#       what a failure means; it only moves bytes to Ollama and back.
#
# Why this exists (4.5f): _run_turn used to fuse transport with the turn
# pipeline. Splitting transport out gives the orchestrator a single, mockable
# seam for the model call and keeps degradation/memory/dispatch policy out of
# the wire layer.

import os

import ollama

from config.settings import MODEL


# One client for the process. Lazy: no connection until the first .chat().
_client = ollama.Client(host=os.getenv("OLLAMA_HOST", "http://localhost:11434"))


def chat(messages: list[dict], options: dict | None = None) -> str:
    """Send messages to Ollama and return the reply content.

    messages — standard Ollama chat list: [{"role": ..., "content": ...}, ...]
    options  — optional Ollama options dict (e.g. {"num_predict": 1}).

    Returns the assistant message content as a string.
    Raises on connection error or malformed response; callers handle policy.
    """
    response = _client.chat(model=MODEL, messages=messages, options=options)
    return response["message"]["content"]