# tests/smoke_4_5f.py
# Stage 4.5f verification — NL dispatch (cut 1 seam + cut 2 wiring).
# Run: python -m tests.smoke_4_5f   (from project root, venv active)
#
# Covers:
#   - ToolRegistry.to_ollama_tools(): opt-in only, slash stripped, schema passed through
#   - ollama_client.chat(): unchanged call shape (no tools/think sent), still returns str
#   - ollama_client.chat_message(): sends tools/think only when given, normalizes tool_calls
#   - nl_dispatch.run_with_tools(): gate on every call, validate on receipt,
#     one repair re-request, decline / handler failure handled, no deadlock path
#   - orchestrator.run_turn(allow_tools=...): default path unchanged, tool turns not persisted
#   - closing cut: A4 lifecycle list covers every PocketModule once; Monitor has no dead param

from unittest.mock import patch

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import core.ollama_client as ollama_client
import core.nl_dispatch as nl_dispatch
from core.tool_registry import ToolRegistry, Tool


def _noop(args):
    pass


def test_to_ollama_tools_opt_in():
    """Only model_callable tools are exported, in Ollama's function-tool shape."""
    reg = ToolRegistry()
    reg.register(Tool(name="/quit", handler=_noop, description="Quit.", aliases=("bye",), exact=True))
    reg.register(Tool(
        name="/read", handler=_noop, description="Read a file.", model_callable=True,
        model_handler=lambda a: "",
        params_schema={
            "type": "object",
            "properties": {"filepath": {"type": "string"}},
            "required": ["filepath"],
        },
    ))
    reg.register(Tool(name="/memory", handler=_noop, description="Count memories.",
                      model_callable=True, model_handler=lambda a: ""))

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


# ── cut 2: nl_dispatch ───────────────────────────────────────────────────────

def _reply(content="", calls=None):
    return {"content": content, "tool_calls": calls or [], "thinking": None}


def _call(name, **arguments):
    return {"name": name, "arguments": arguments}


def _dispatch_registry(read_fn):
    reg = ToolRegistry()
    reg.register(Tool(
        name="/read", handler=_noop, description="Read a file.",
        model_callable=True, model_handler=read_fn,
        params_schema={
            "type": "object",
            "properties": {"filepath": {"type": "string", "minLength": 1}},
            "required": ["filepath"],
            "additionalProperties": False,
        },
    ))
    return reg


def test_register_requires_model_handler():
    """model_callable without a model_handler must be refused at registration."""
    reg = ToolRegistry()
    try:
        reg.register(Tool(name="/x", handler=_noop, description="x", model_callable=True))
    except ValueError:
        print("PASS register — model_callable without model_handler refused")
        return
    raise AssertionError("registry accepted a model_callable tool with no model_handler")


def test_no_tool_call_passthrough():
    """A plain reply passes straight through; the gate is never touched."""
    reg = _dispatch_registry(lambda a: "x")
    with patch("core.nl_dispatch.chat_message", return_value=_reply("hey there")) as cm, \
         patch("core.nl_dispatch.propose_action") as gate:
        reply, extra, ran = nl_dispatch.run_with_tools([{"role": "user", "content": "hi"}], reg)

    assert (reply, extra, ran) == ("hey there", [], False), (reply, extra, ran)
    assert cm.call_args.kwargs["tools"][0]["function"]["name"] == "read", "tools not offered"
    assert not gate.called, "gate fired with no tool call"
    print("PASS run_with_tools — plain reply, no gate")


def test_approved_call_runs():
    """Valid call → gate → handler → result back to the model → final answer."""
    seen = []
    reg = _dispatch_registry(lambda a: seen.append(a) or "line one")
    replies = [_reply(calls=[_call("read", filepath="notes.txt")]), _reply("It says line one.")]
    msgs = [{"role": "user", "content": "read notes.txt"}]

    with patch("core.nl_dispatch.chat_message", side_effect=replies) as cm, \
         patch("core.nl_dispatch.propose_action", return_value=True) as gate:
        reply, extra, ran = nl_dispatch.run_with_tools(msgs, reg)

    assert reply == "It says line one." and ran is True
    assert seen == [{"filepath": "notes.txt"}], f"handler args: {seen}"
    assert gate.call_args.args[1] == "notes.txt", f"gate saw command {gate.call_args.args[1]!r}"
    assert "/read" in gate.call_args.args[0], "description must name /read so the read denylist runs"
    assert [m["role"] for m in extra] == ["assistant", "tool"], extra
    assert "tools" not in cm.call_args_list[1].kwargs, "follow-up call must not offer tools"
    assert len(msgs) == 1, "run_with_tools mutated the caller's messages"
    print("PASS run_with_tools — approved call ran, result fed back, one call per turn")


def test_declined_call_does_not_run():
    """A 'n' at the gate means the handler never runs."""
    seen = []
    reg = _dispatch_registry(lambda a: seen.append(a) or "x")
    replies = [_reply(calls=[_call("read", filepath="notes.txt")]), _reply("Okay, I won't.")]

    with patch("core.nl_dispatch.chat_message", side_effect=replies), \
         patch("core.nl_dispatch.propose_action", return_value=False):
        reply, extra, ran = nl_dispatch.run_with_tools([{"role": "user", "content": "read it"}], reg)

    assert seen == [] and ran is False and reply == "Okay, I won't."
    assert "declined" in extra[-1]["content"]
    print("PASS run_with_tools — declined call never executed")


def test_malformed_call_repaired_once():
    """Bad args → one re-request with the error → valid call → gate → run."""
    seen = []
    reg = _dispatch_registry(lambda a: seen.append(a) or "ok")
    replies = [
        _reply(calls=[_call("read", path="notes.txt")]),        # wrong key
        _reply(calls=[_call("read", filepath="notes.txt")]),    # repaired
        _reply("Done."),
    ]
    with patch("core.nl_dispatch.chat_message", side_effect=replies) as cm, \
         patch("core.nl_dispatch.propose_action", return_value=True) as gate:
        reply, extra, ran = nl_dispatch.run_with_tools([{"role": "user", "content": "read"}], reg)

    assert seen == [{"filepath": "notes.txt"}] and ran and reply == "Done."
    assert gate.call_count == 1, "gate must only see the valid call"
    assert "ERROR" in extra[1]["content"], "repair message missing"
    assert "tools" in cm.call_args_list[1].kwargs, "repair re-request must offer tools again"
    print("PASS run_with_tools — malformed call re-requested once, then ran")


def test_unknown_args_dropped():
    """Invented extra args are dropped, the call still validates and goes to the gate."""
    seen = []
    reg = _dispatch_registry(lambda a: seen.append(a) or "ok")
    replies = [_reply(calls=[_call("read", filepath="notes.txt", db_name="ChromaDB")]), _reply("Done.")]

    with patch("core.nl_dispatch.chat_message", side_effect=replies), \
         patch("core.nl_dispatch.propose_action", return_value=True) as gate:
        reply, extra, ran = nl_dispatch.run_with_tools([{"role": "user", "content": "read"}], reg)

    assert seen == [{"filepath": "notes.txt"}], f"handler args: {seen}"
    assert gate.call_args.args[1] == "notes.txt", "dropped arg leaked into the gate command"
    assert ran and reply == "Done."
    print("PASS run_with_tools — invented extra args dropped, call gated and ran")


def test_malformed_twice_never_runs():
    """Still bad after the repair → answer without tools; handler and gate untouched."""
    seen = []
    reg = _dispatch_registry(lambda a: seen.append(a) or "x")
    replies = [
        _reply(calls=[_call("read")]),
        _reply(calls=[_call("delete_everything", target="C:/")]),  # unknown tool
        _reply("Sorry, I couldn't do that."),
    ]
    with patch("core.nl_dispatch.chat_message", side_effect=replies) as cm, \
         patch("core.nl_dispatch.propose_action") as gate:
        reply, extra, ran = nl_dispatch.run_with_tools([{"role": "user", "content": "x"}], reg)

    assert seen == [] and not gate.called and ran is False
    assert reply == "Sorry, I couldn't do that."
    assert "tools" not in cm.call_args_list[2].kwargs, "final call must not offer tools"
    print("PASS run_with_tools — bad twice: fails closed, nothing executed")


def test_handler_failure_reported():
    """A handler that raises after approval reports back; the turn survives."""
    def boom(a):
        raise OSError("disk on fire")
    reg = _dispatch_registry(boom)
    replies = [_reply(calls=[_call("read", filepath="x.txt")]), _reply("That failed.")]

    with patch("core.nl_dispatch.chat_message", side_effect=replies), \
         patch("core.nl_dispatch.propose_action", return_value=True):
        reply, extra, ran = nl_dispatch.run_with_tools([{"role": "user", "content": "x"}], reg)

    assert "disk on fire" in extra[-1]["content"] and reply == "That failed."
    print("PASS run_with_tools — handler failure reported, no crash")


# ── cut 2: orchestrator wiring ───────────────────────────────────────────────

def test_run_turn_paths():
    """allow_tools=False keeps the old chat() path; a tool turn isn't persisted."""
    import core.orchestrator as orchestrator

    common = [
        patch("core.orchestrator.bus"),  # 4.5g: output goes over the bus
        patch("core.orchestrator.get_relevant_memories", return_value=""),
    ]
    for p in common:
        p.start()
    try:
        # Default path: plain chat(), persisted, run_with_tools untouched.
        orchestrator.session_history.clear()
        with patch("core.orchestrator.chat", return_value="plain") as ch, \
             patch("core.orchestrator.run_with_tools") as rwt, \
             patch("core.orchestrator.save_memory") as save:
            orchestrator.run_turn("hello")
        assert ch.called and not rwt.called, "default turn left the chat() path"
        assert save.call_count == 2, "default turn not persisted"

        # Tool path: tool ran → history keeps the tool messages, nothing persisted.
        orchestrator.session_history.clear()
        tool_msgs = [{"role": "assistant", "content": "", "tool_calls": []},
                     {"role": "tool", "tool_name": "read", "content": "file text"}]
        with patch("core.orchestrator.chat") as ch, \
             patch("core.orchestrator.run_with_tools", return_value=("summary", tool_msgs, True)) as rwt, \
             patch("core.orchestrator.save_memory") as save:
            orchestrator.run_turn("read notes.txt", allow_tools=True)
        assert rwt.called and not ch.called
        assert not save.called, "tool turn leaked into vector memory"
        roles = [m["role"] for m in orchestrator.session_history]
        assert roles == ["user", "assistant", "tool", "assistant"], roles
        assert "Tools:" in rwt.call_args.args[0][0]["content"], "TOOL_GUIDANCE missing from system prompt"
    finally:
        for p in common:
            p.stop()
        orchestrator.session_history.clear()
    print("PASS run_turn — default path unchanged; tool turn kept in history, not persisted")


# ── closing cut: A4 lifecycle + dead Monitor param ──────────────────────────

def test_lifecycle_covers_all_modules():
    """Every PocketModule singleton is in pocket.LIFECYCLE exactly once, logger first."""
    import inspect
    import pocket
    from core.pocket_module import PocketModule

    lc = pocket.LIFECYCLE
    assert lc[0] is pocket.logger_module, "logger must start first (and stop last)"
    assert len({id(m) for m in lc}) == len(lc), "a module is listed twice (double start)"
    assert all(isinstance(m, PocketModule) for m in lc), "non-PocketModule in LIFECYCLE"

    covered = {type(m) for m in lc}
    missing = [c.__name__ for c in PocketModule.__subclasses__()
               if c not in covered and c.__module__.startswith("core.")]
    assert not missing, f"PocketModules not in LIFECYCLE: {missing}"

    src = inspect.getsource(pocket.main)
    assert "tts_worker" not in src, "main() still hand-starts the tts worker"
    print(f"PASS lifecycle — {len(lc)} modules, each once, logger first, no hand-wired tts worker")


def test_monitor_dead_param_gone():
    """create_monitor / ServiceMonitor no longer take send_to_avatar_fn."""
    import inspect
    from core.monitor import ServiceMonitor, create_monitor

    for fn in (ServiceMonitor.__init__, create_monitor):
        assert "send_to_avatar_fn" not in inspect.signature(fn).parameters, f"{fn.__qualname__} still has it"
    print("PASS monitor — dead send_to_avatar_fn param removed")


if __name__ == "__main__":
    test_to_ollama_tools_opt_in()
    test_chat_call_shape_unchanged()
    test_chat_message_tools_and_think()
    test_chat_message_no_tool_calls()
    test_register_requires_model_handler()
    test_no_tool_call_passthrough()
    test_approved_call_runs()
    test_declined_call_does_not_run()
    test_malformed_call_repaired_once()
    test_unknown_args_dropped()
    test_malformed_twice_never_runs()
    test_handler_failure_reported()
    test_run_turn_paths()
    test_lifecycle_covers_all_modules()
    test_monitor_dead_param_gone()
    print("\nAll 4.5f NL-dispatch checks passed.")
