# tests/degradation_test.py
# Stage 4k — Graceful Degradation fault-injection test.
#
# Breaks each service at its dependency boundary (no Docker/exe juggling),
# drives the real wrapped function, and asserts the degradation contract:
#   - the call returns instead of raising
#   - state.health[service] flips to False
#   - is_degraded(service) is True
#   - a "system.degraded" event fires
# then clears the fault and asserts recovery.
#
# Run from the project root:  python tests/degradation_test.py
#
# NOTE: this verifies the *contract*, not physical behavior (avatar actually
# going neutral, Piper actually silent). Do one manual pass for that.

import os
import sys
import subprocess

# Make the project root importable when run as `python tests/degradation_test.py`
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import core.llm as llm
import core.memory as memory
import core.tts as tts
from core.state_manager import state
from core.event_bus import bus
from core.degradation import is_degraded

# ── Bus event capture ─────────────────────────────────────────────────────────
_events = []
bus.subscribe("system.degraded",  lambda e: _events.append(("degraded",  e["service"])))
bus.subscribe("system.recovered", lambda e: _events.append(("recovered", e["service"])))

def _saw(kind, service):
    return (kind, service) in _events

# ── Result tracking ───────────────────────────────────────────────────────────
_passed = 0
_failed = 0

def check(label, condition):
    global _passed, _failed
    if condition:
        print(f"  ✅ {label}")
        _passed += 1
    else:
        print(f"  ❌ {label}")
        _failed += 1

# ── Fakes ─────────────────────────────────────────────────────────────────────
class _DeadCollection:
    def query(self, *a, **k): raise RuntimeError("injected: chroma down")
    def add(self, *a, **k):   raise RuntimeError("injected: chroma down")


# ═════════════════════════════════════════════════════════════════════════════
# OLLAMA
# ═════════════════════════════════════════════════════════════════════════════

def test_ollama():
    print("\n[Ollama]")
    real_client = llm.ollama_client
    real_save   = llm.save_memory
    llm.save_memory = lambda *a, **k: None   # don't pollute memory with test text
    try:
        # ---- Fault ----
        _events.clear()
        class _Dead:
            def chat(self, *a, **k): raise RuntimeError("injected: ollama unreachable")
        llm.ollama_client = _Dead()

        crashed = False
        try:
            llm.handle_user_input_sync("degradation test message")
        except Exception:
            crashed = True
        check("handle_user_input_sync did not crash", not crashed)
        check("health.ollama == False", state.get("health", "ollama") is False)
        check("is_degraded('ollama')", is_degraded("ollama"))
        check("system.degraded fired", _saw("degraded", "ollama"))

        # ---- Recovery (faked success, no live Ollama needed) ----
        _events.clear()
        class _Ok:
            def chat(self, *a, **k): return {"message": {"content": "ok"}}
        llm.ollama_client = _Ok()

        crashed = False
        try:
            llm.handle_user_input_sync("recovery probe")
        except Exception:
            crashed = True
        check("recovery call did not crash", not crashed)
        check("health.ollama == True", state.get("health", "ollama") is True)
        check("not is_degraded('ollama')", not is_degraded("ollama"))
        check("system.recovered fired", _saw("recovered", "ollama"))
    finally:
        llm.ollama_client = real_client
        llm.save_memory   = real_save


# ═════════════════════════════════════════════════════════════════════════════
# CHROMA
# ═════════════════════════════════════════════════════════════════════════════

def test_chroma():
    print("\n[Chroma]")
    real = memory.memory
    try:
        memory.memory = _DeadCollection()

        # Read path
        _events.clear()
        result = memory.get_relevant_memories("anything")
        check("get_relevant_memories returned '' on failure", result == "")
        check("health.chroma == False", state.get("health", "chroma") is False)
        check("is_degraded('chroma')", is_degraded("chroma"))
        check("system.degraded fired", _saw("degraded", "chroma"))

        # Write path — must not crash, and must dedup (no second event)
        _events.clear()
        crashed = False
        try:
            memory.save_memory("user", "x" * 40)   # >20 chars so it isn't skipped
        except Exception:
            crashed = True
        check("save_memory did not crash while degraded", not crashed)
        check("save_memory deduped (no new degraded event)", not _saw("degraded", "chroma"))
    finally:
        memory.memory = real

    # Recovery via the read detector (embedded PersistentClient — read-only, no pollution)
    _events.clear()
    memory.get_relevant_memories("recovery probe")
    check("health.chroma == True", state.get("health", "chroma") is True)
    check("not is_degraded('chroma')", not is_degraded("chroma"))
    check("system.recovered fired", _saw("recovered", "chroma"))


# ═════════════════════════════════════════════════════════════════════════════
# PIPER
# ═════════════════════════════════════════════════════════════════════════════

def test_piper():
    print("\n[Piper]")
    real_exe = tts.PIPER_EXE
    try:
        # ---- Fault: missing executable ----
        _events.clear()
        tts.PIPER_EXE = r"C:\nonexistent\piper.exe"
        crashed = False
        try:
            tts.run_piper_tts("hello")
        except Exception:
            crashed = True
        check("run_piper_tts did not crash with missing exe", not crashed)
        check("health.piper == False", state.get("health", "piper") is False)
        check("is_degraded('piper')", is_degraded("piper"))
        check("system.degraded fired", _saw("degraded", "piper"))
    finally:
        tts.PIPER_EXE = real_exe

    # ---- Recovery: real exe path + stubbed subprocess/audio so nothing plays ----
    _events.clear()
    real_popen = subprocess.Popen
    real_play  = tts.sd.play
    real_wait  = tts.sd.wait
    real_exe2  = tts.PIPER_EXE
    try:
        class _FakeProc:
            def communicate(self, input=None):
                return (b"\x00\x00", None)
        subprocess.Popen = lambda *a, **k: _FakeProc()
        tts.sd.play = lambda *a, **k: None
        tts.sd.wait = lambda *a, **k: None
        tts.PIPER_EXE = sys.executable   # any real file passes the exists() guard
        tts.run_piper_tts("recovery")
        check("health.piper == True", state.get("health", "piper") is True)
        check("not is_degraded('piper')", not is_degraded("piper"))
        check("system.recovered fired", _saw("recovered", "piper"))
    finally:
        subprocess.Popen = real_popen
        tts.sd.play = real_play
        tts.sd.wait = real_wait
        tts.PIPER_EXE = real_exe2


# ═════════════════════════════════════════════════════════════════════════════
# WEBSOCKET
# ═════════════════════════════════════════════════════════════════════════════

def test_websocket():
    print("\n[WebSocket]")
    from core.degradation import on_websocket_degraded, on_websocket_connected

    # Wire the handlers to the same 4n events pocket.py subscribes them to,
    # then emit as the reconnection engine would.
    bus.subscribe("connection.websocket.degraded",  on_websocket_degraded)
    bus.subscribe("connection.websocket.connected", on_websocket_connected)

    # ---- Fault: 4n gave up (DEGRADED_MODE) ----
    _events.clear()
    bus.emit("connection.websocket.degraded", {"reason": "injected"})
    check("expression set to neutral", state.expression == "neutral")
    check("health.websocket == False", state.get("health", "websocket") is False)
    check("is_degraded('websocket')", is_degraded("websocket"))
    check("system.degraded fired", _saw("degraded", "websocket"))

    # ---- Recovery: reconnect ----
    _events.clear()
    bus.emit("connection.websocket.connected", {"attempt": 1})
    check("health.websocket == True", state.get("health", "websocket") is True)
    check("not is_degraded('websocket')", not is_degraded("websocket"))
    check("system.recovered fired", _saw("recovered", "websocket"))


# ═════════════════════════════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════════════════════════════

def main():
    print("\n=== Stage 4k — Graceful Degradation fault-injection test ===")
    test_ollama()
    test_chroma()
    test_piper()
    test_websocket()
    print(f"\n=== {_passed} passed, {_failed} failed ===\n")
    sys.exit(1 if _failed else 0)


if __name__ == "__main__":
    main()