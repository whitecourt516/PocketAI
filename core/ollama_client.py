# core/ollama_client.py
# Pure Ollama transport. The only place a raw ollama.chat() call lives.
#
# Public API:
#   chat(messages, options=None) -> str
#       Send messages to Ollama, return the reply content as a string.
#       Raises on transport error or malformed response — callers decide
#       policy (degradation, retry, etc.). This module has no opinion on
#       what a failure means; it only moves bytes to Ollama and back.
#   chat_message(messages, options=None, tools=None, think=None) -> dict
#       Same call, but returns the whole reply message as a plain dict:
#       {"content": str, "tool_calls": [{"name", "arguments"}], "thinking": str|None}.
#       tools / think are only sent when given (4.5f NL dispatch seam).
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
    return chat_message(messages, options)["content"]


def chat_message(
    messages: list[dict],
    options: dict | None = None,
    tools: list[dict] | None = None,
    think: bool | None = None,
) -> dict:
    """Send messages to Ollama and return the full reply message as a plain dict.

    tools — Ollama `tools` array (see ToolRegistry.to_ollama_tools()).
    think — False turns off reasoning on thinking models (Qwen3 / Qwen3.5).
            Left as None, nothing is sent and the model default applies.

    Returns {"content": str, "tool_calls": list[dict], "thinking": str | None}.
    Each tool call is {"name": str, "arguments": dict}. Arguments are NOT
    validated here: Ollama doesn't check them against the schema, and this
    module has no opinion on policy. Validate on receipt in the caller.
    """
    kwargs = {"model": MODEL, "messages": messages, "options": options}
    if tools is not None:
        kwargs["tools"] = tools
    if think is not None:
        kwargs["think"] = think

    response = _client.chat(**kwargs)
    message  = response["message"]

    tool_calls = []
    for call in message.get("tool_calls") or []:
        fn = call["function"]
        tool_calls.append({"name": fn["name"], "arguments": dict(fn["arguments"] or {})})

    return {
        "content":    message["content"] or "",
        "tool_calls": tool_calls,
        "thinking":   message.get("thinking"),
    }