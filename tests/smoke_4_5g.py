# tests/smoke_4_5g.py
# Stage 4.5g verification — conversation / avatar / TTS path committed to the event bus.
# Run: python -m tests.smoke_4_5g   (from project root, venv active)
#
# Covers:
#   - run_turn emits its output in order: thinking → wander_pause → avatar text → voice
#   - an Ollama failure emits wander_resume and never speaks
#   - degradation.notify reaches avatar + voice over the bus; skips voice when Piper is down
#   - pocket.EVENT_WIRING routes every output event to the right module, once each
#   - no lazy `from core.` imports left in the modules 4.5g touched

import inspect
import re
from unittest.mock import patch

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import core.degradation as degradation
import core.orchestrator as orchestrator
from core.event_bus import bus
from core.state_manager import state

OUTPUT_EVENTS = ("websocket.send", "avatar_router.send", "tts.speak")


class Recorder:
    """Subscribes to the output events on the REAL bus and records them in order."""

    def __init__(self):
        self.events = []

    def __call__(self, event):
        self.events.append(event)

    def __enter__(self):
        for et in OUTPUT_EVENTS:
            bus.subscribe(et, self)
        return self

    def __exit__(self, *exc):
        for et in OUTPUT_EVENTS:
            bus.unsubscribe(et, self)

    def summary(self):
        out = []
        for e in self.events:
            if e["type"] == "websocket.send":
                out.append(("ws", e["data"].get("type")))
            else:
                out.append((e["type"], e.get("text")))
        return out


def test_turn_output_order():
    """A normal turn emits expression/pause first, then avatar text, then voice."""
    orchestrator.session_history.clear()
    with patch("core.orchestrator.chat", return_value="hello there"), \
         patch("core.orchestrator.get_relevant_memories", return_value=""), \
         patch("core.orchestrator.save_memory"), \
         Recorder() as rec:
        orchestrator.run_turn("hi")
    orchestrator.session_history.clear()

    assert rec.summary() == [
        ("ws", "expression"),
        ("ws", "wander_pause"),
        ("avatar_router.send", "hello there"),
        ("tts.speak", "hello there"),
    ], rec.summary()
    print("PASS turn order — thinking → pause → avatar text → voice")


def test_turn_failure_resumes_and_stays_quiet():
    """Ollama down: wander_resume goes out, nothing is spoken or routed to the avatar."""
    def dead(*a, **k):
        raise RuntimeError("injected: ollama down")

    with patch("core.orchestrator.chat", side_effect=dead), \
         patch("core.orchestrator.get_relevant_memories", return_value=""), \
         patch("core.orchestrator.mark_degraded"), \
         Recorder() as rec:
        orchestrator.run_turn("hi")

    kinds = rec.summary()
    assert ("ws", "wander_resume") in kinds, kinds
    assert not any(k[0] in ("avatar_router.send", "tts.speak") for k in kinds), kinds
    print("PASS turn failure — wander_resume sent, no voice / avatar text")


def test_notify_over_bus():
    """notify() → avatar expression + speech bubble + voice, all via the bus."""
    with patch.object(state, "get", return_value=True), Recorder() as rec:
        degradation.notify("test message", expression="concerned")
    assert rec.summary() == [
        ("ws", "expression"),
        ("ws", "speech"),
        ("tts.speak", "test message"),
    ], rec.summary()

    with patch.object(state, "get", return_value=False), Recorder() as rec:  # Piper down
        degradation.notify("no voice please")
    assert ("tts.speak", "no voice please") not in rec.summary(), rec.summary()
    print("PASS notify — avatar + voice over the bus; voice skipped when Piper is down")


def test_event_wiring():
    """Each output event goes to exactly the module that owns it, once."""
    import pocket

    wiring = pocket.EVENT_WIRING
    assert len(wiring) == len(set(wiring)), "duplicate subscription in EVENT_WIRING"

    def targets(event_type):
        return [h for et, h in wiring if et == event_type]

    assert targets("websocket.send")     == [pocket.websocket_module.on_event]
    assert targets("avatar_router.send") == [pocket.avatar_router_module.on_event]
    assert targets("tts.speak")          == [pocket.tts_module.on_event]
    print(f"PASS wiring — {len(wiring)} subscriptions, output events each routed once")


def test_no_lazy_imports():
    """The 4.5g modules import their dependencies at the top, not inside functions."""
    import core.web_search as web_search
    import core.logger as logger

    for mod in (orchestrator, degradation, web_search, logger):
        src = inspect.getsource(mod)
        lazy = re.findall(r"^[ \t]+from core\.\S+ import .+$", src, re.M)
        assert not lazy, f"{mod.__name__} still has lazy imports: {lazy}"
    print("PASS no lazy imports — orchestrator, degradation, web_search, logger")


if __name__ == "__main__":
    test_turn_output_order()
    test_turn_failure_resumes_and_stays_quiet()
    test_notify_over_bus()
    test_event_wiring()
    test_no_lazy_imports()
    print("\nAll 4.5g event-bus checks passed.")
