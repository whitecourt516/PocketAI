# tests/smoke_4_5f.py
# Stage 4.5f verification — NL dispatch seam (cut 1, no behavior change).
# Run: python -m tests.smoke_4_5f   (from project root, venv active)
#
# Covers:
#   - ToolRegistry.to_ollama_tools(): opt-in only, slash stripped, schema passed through
#   - ollama_client.chat(): unchanged call shape (no tools/think sent), still returns str
#   - ollama_client.chat_message(): sends tools/think only when given, normalizes tool_calls

from unittest.mock import patch

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import core.ollama_client as ollama_client
from core.tool_registry import ToolRegistry, Tool


def _noop(args):
    pass


def test_to_ollama_tools_opt_in():
    """Only model_callable tools are exported, in Ollama's function-tool shape."""
    reg = ToolRegistry()
    reg.register(Tool(name="/quit", handler=_noop, description="Quit.", aliases=("bye",), exact=True))
    reg.register(Tool(
        name="/read", handler=_noop, description="Read a file.", model_callable=True,
        params_schema={
            "type": "object",
            "properties": {"filepath": {"type": "string"}},
            "required": ["filepath"],
        },
    ))
    reg.register(Tool(name="/memory", handler=_noop, description="Count memories.", model_callable=True))

    tools = reg.to_ollama_tools()
    names = [t["function"]["name"] for t in tools]

    assert names == ["read", "memory"], f"unexpected exported tools: {names}"
    assert all(t["type"] == "function" for t in tools)
    assert tools[0]["function"]["parameters"]["required"] == ["filepath"], "schema not passed through"
    assert tools[1]["function"]["parameters"] == {"type": "object", "properties": {}}, "empty schema not defaulted"
    print("PASS to_ollama_tools — opt-in only, slash stripped, schema passed through")


def test_chat_call_shape_unchanged():
    """chat() must send exactly what it sent before this cut, and return a string."""
    fake = {"message": {"role": "assistant", "content": "hi"}}
    with patch.object(ollama_client._client, "chat", return_value=fake) as mock_chat:
        out = ollama_client.chat([{"role": "user", "content": "hello"}])

    assert out == "hi", f"chat() returned {out!r}"
    sent = mock_chat.call_args.kwargs
    assert set(sent) == {"model", "messages", "options"}, f"chat() sent extra keys: {set(sent)}"
    print("PASS chat — call shape unchanged, returns content string")


def test_chat_message_tools_and_think():
    """chat_message() forwards tools/think when given and normalizes tool_calls."""
    fake = {"message": {
        "role": "assistant",
        "content": "",
        "thinking": None,
        "tool_calls": [{"function": {"name": "read", "arguments": {"filepath": "notes.txt"}}}],
    }}
    tools = [{"type": "function", "function": {"name": "read", "description": "", "parameters": {}}}]

    with patch.object(ollama_client._client, "chat", return_value=fake) as mock_chat:
        msg = ollama_client.chat_message([{"role": "user", "content": "read notes"}], tools=tools, think=False)

    sent = mock_chat.call_args.kwargs
    assert sent["tools"] == tools, "tools not forwarded"
    assert sent["think"] is False, "think not forwarded"
    assert msg["tool_calls"] == [{"name": "read", "arguments": {"filepath": "notes.txt"}}], msg["tool_calls"]
    assert msg["content"] == ""
    print("PASS chat_message — tools/think forwarded, tool_calls normalized")


def test_chat_message_no_tool_calls():
    """A plain reply comes back with an empty tool_calls list, not None."""
    fake = {"message": {"role": "assistant", "content": "just talking"}}
    with patch.object(ollama_client._client, "chat", return_value=fake):
        msg = ollama_client.chat_message([{"role": "user", "content": "hey"}])

    assert msg == {"content": "just talking", "tool_calls": [], "thinking": None}, msg
    print("PASS chat_message — plain reply, empty tool_calls")


if __name__ == "__main__":
    test_to_ollama_tools_opt_in()
    test_chat_call_shape_unchanged()
    test_chat_message_tools_and_think()
    test_chat_message_no_tool_calls()
    print("\nAll 4.5f NL-dispatch seam checks passed.")
