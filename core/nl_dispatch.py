# core/nl_dispatch.py
# Natural-language tool dispatch — implements ADR-001 (4.5f).
#
# Public API:
#   TOOL_GUIDANCE                         — system-prompt addendum when tools are offered
#   run_with_tools(messages, reg=registry) -> (reply, tool_messages, tool_ran)
#
# Flow (one tool call per turn for now):
#   model reply → tool call? → look up in registry → validate args against
#   params_schema → propose_action() y/n → model_handler(args) → result back
#   to the model → final answer (no tools offered on that last call).
#
# Hard rules (impr. #2 / #3, ADR-001):
#   - model invocation ≠ approval: EVERY model call goes through propose_action(),
#     whatever the tool's risk level.
#   - Ollama doesn't validate arguments; we do, on receipt. A malformed call gets
#     one repair re-request, then the model must answer without tools. A bad call
#     is never "best-effort" executed.
#   - The only try/except around execution is AFTER approval, to report a handler
#     failure back to the model instead of killing the turn. It is not a fallback
#     path around the gate.
#
# Transport errors (Ollama down) are NOT caught here — they propagate to
# run_turn, which owns degradation policy.

import jsonschema

from core.config_loader import CFG
from core.ollama_client import chat_message
from core.permissions import propose_action
from core.tool_registry import registry


MAX_REPAIRS = 1  # re-requests allowed for a malformed / unknown tool call

_USER = CFG.get("user_name") or "the user"

TOOL_GUIDANCE = (
    f"Tools: call a tool ONLY when {_USER}'s message clearly asks for something "
    "a tool does (reading a file they name, searching the web, checking how many "
    "memories are stored). For normal conversation, answer directly and do not "
    f"call any tool. Every tool call is shown to {_USER} for approval before it runs."
)

_EMPTY_SCHEMA = {"type": "object", "properties": {}}


def validate_call(call: dict, reg=registry):
    """Return (tool, args, None) for a valid call, or (tool_or_None, None, error_text).

    Arguments the schema doesn't declare are dropped BEFORE validation (8B
    models invent extras, e.g. memory(db_name="ChromaDB")). Dropping can only
    remove input, never add it, and the gate still shows the final args, so it
    doesn't soften the boundary. Missing or wrong-typed args still fail.
    """
    tool = reg.get_function(call.get("name", ""))
    if tool is None:
        available = ", ".join(t["function"]["name"] for t in reg.to_ollama_tools())
        return None, None, f"unknown tool '{call.get('name')}'. Available tools: {available}"

    schema  = tool.params_schema or _EMPTY_SCHEMA
    raw     = call.get("arguments") or {}
    known   = schema.get("properties", {})
    args    = {k: v for k, v in raw.items() if k in known}
    dropped = sorted(set(raw) - set(args))
    if dropped:
        print(f"  [NL dispatch: ignored unknown args for {tool.name}: {', '.join(dropped)}]")

    try:
        jsonschema.validate(args, schema)
    except jsonschema.ValidationError as e:
        return tool, None, f"invalid arguments for '{call['name']}': {e.message}"

    return tool, args, None


def _proposal(tool, args: dict):
    """(description, command) for propose_action().

    command is the bare argument value(s) so the gate's own checks see the real
    thing: the executor denylist runs on it, and for /read the read denylist
    runs on the path (triggered by "/read" in the description).
    """
    description = f"Run {tool.name} (proposed by Pocket): {tool.description}"
    values = [str(v) for v in args.values()]
    command = " ".join(values) if values else tool.name
    return description, command


def _execute(tool, args: dict):
    """Gate, then run. Returns (text for the model, ran)."""
    description, command = _proposal(tool, args)
    if not propose_action(description, command):
        return f"{_USER} declined the {tool.name} call. Do not retry it; answer without it.", False

    try:
        return tool.model_handler(args), True
    except Exception as e:
        return f"The {tool.name} tool failed: {e}", True


def _assistant_call(msg: dict, call: dict) -> dict:
    return {
        "role": "assistant",
        "content": msg["content"],
        "tool_calls": [{"function": {"name": call["name"], "arguments": call["arguments"]}}],
    }


def _tool_result(name: str, content: str) -> dict:
    return {"role": "tool", "tool_name": name, "content": content}


def run_with_tools(messages: list[dict], reg=registry):
    """Run the model with tools offered. Does not mutate `messages`.

    Returns (reply, tool_messages, tool_ran):
      reply          — final assistant text
      tool_messages  — assistant tool_call + tool result messages from this
                       turn, for session_history (so follow-ups can see them)
      tool_ran       — True if an approved tool actually executed
    """
    specs = reg.to_ollama_tools()
    if not specs:
        return chat_message(messages)["content"], [], False

    convo = list(messages)
    extra = []
    tool_ran = False
    repairs = 0

    msg = chat_message(convo, tools=specs)

    while msg["tool_calls"]:
        call = msg["tool_calls"][0]  # one call per turn; extras are ignored
        tool, args, error = validate_call(call, reg)

        step = [_assistant_call(msg, call)]

        if error:
            print(f"  [NL dispatch: rejected tool call: {error}]")
            if repairs < MAX_REPAIRS:
                repairs += 1
                step.append(_tool_result(call.get("name", "?"),
                            f"ERROR: {error}. Fix the call, or answer without a tool."))
                convo += step
                extra += step
                msg = chat_message(convo, tools=specs)
                continue

            step.append(_tool_result(call.get("name", "?"),
                        f"ERROR: {error}. No more tool calls this turn; answer directly."))
            convo += step
            extra += step
            msg = chat_message(convo)  # no tools: must answer in words
            break

        result, ran = _execute(tool, args)
        tool_ran = tool_ran or ran
        step.append(_tool_result(call["name"], result))
        convo += step
        extra += step
        msg = chat_message(convo)  # no tools on the follow-up: one call per turn
        break

    return msg["content"], extra, tool_ran
