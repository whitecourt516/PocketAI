# tests/smoke_test.py
# Stage 4a.1 — Smoke test suite
#
# Confirms all core systems are alive after any change.
# Run before and after significant changes:
#   python tests/smoke_test.py
#
# Add entries here as new systems come online.

import os
import sys
import time
import uuid

# ── Path setup ────────────────────────────────────────────────────────────────
script_dir   = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(script_dir, '..')
sys.path.insert(0, project_root)

PASS = "✅"
FAIL = "❌"
SKIP = "⏭ "

results = []


def check(label, fn):
    try:
        fn()
        results.append((PASS, label, None))
        print(f"  {PASS} {label}")
    except Exception as e:
        results.append((FAIL, label, str(e)))
        print(f"  {FAIL} {label} — {e}")


def skip(label, reason):
    results.append((SKIP, label, reason))
    print(f"  {SKIP} {label} — {reason}")


# ═════════════════════════════════════════════════════════════════════════════
# TESTS
# ═════════════════════════════════════════════════════════════════════════════

print("\n  Running Pocket smoke tests...\n")


# ── Ollama ────────────────────────────────────────────────────────────────────
def test_ollama():
    import ollama
    from config.settings import MODEL
    client   = ollama.Client(host=os.getenv("OLLAMA_HOST", "http://localhost:11434"))
    response = client.chat(
        model=MODEL,
        messages=[{"role": "user", "content": "Reply with the single word: online"}]
    )
    reply = response["message"]["content"].strip()
    assert reply, "Empty response from Ollama"

check("Ollama responds", test_ollama)


# ── ChromaDB ──────────────────────────────────────────────────────────────────
def test_chromadb():
    import chromadb
    chroma_path = os.path.join(project_root, "chroma_data")
    client      = chromadb.PersistentClient(path=chroma_path)
    collection  = client.get_or_create_collection("smoke_test_tmp")
    test_id     = f"smoke-{uuid.uuid4()}"
    test_doc    = "Smoke test entry — safe to delete"

    collection.add(documents=[test_doc], ids=[test_id])
    result = collection.query(query_texts=["smoke test"], n_results=1)

    assert result["documents"][0], "No results returned from ChromaDB"
    assert any(test_doc in d for d in result["documents"][0]), "Test doc not retrieved"

    collection.delete(ids=[test_id])

check("ChromaDB stores and retrieves", test_chromadb)


# ── Piper TTS ─────────────────────────────────────────────────────────────────
def test_piper():
    import subprocess
    import numpy as np
    import sounddevice as sd

    piper_exe   = os.path.join(project_root, "piper", "piper.exe")
    piper_model = os.path.join(project_root, "piper", "voices", "en_US-lessac-medium.onnx")

    assert os.path.exists(piper_exe),   f"Piper exe not found: {piper_exe}"
    assert os.path.exists(piper_model), f"Piper model not found: {piper_model}"

    proc = subprocess.Popen(
        [piper_exe, "--model", piper_model, "--output-raw"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    raw, _ = proc.communicate(input=b"Smoke test.")
    assert len(raw) > 0, "Piper returned empty audio"

    audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    sd.play(audio, samplerate=22050)
    sd.wait()

check("Piper TTS speaks", test_piper)


# ── WebSocket ─────────────────────────────────────────────────────────────────
def test_websocket():
    import asyncio
    import websockets
    import websockets.connection

    AVATAR_WS_URL = "ws://localhost:7845"

    async def _connect():
        async with websockets.connect(AVATAR_WS_URL, open_timeout=3) as ws:
            assert ws.state == websockets.connection.State.OPEN, "WebSocket opened but reports closed"

    asyncio.run(_connect())

check("WebSocket connects to Electron avatar", test_websocket)


# ── /read command ─────────────────────────────────────────────────────────────
def test_read_command():
    from pathlib import Path
    from core.config_loader import is_read_allowed

    allowed = Path(project_root) / "pocket.py"
    assert allowed.exists(), "pocket.py not found"
    assert is_read_allowed(str(allowed)), "pocket.py should be allowed"
    content = allowed.read_text(encoding="utf-8")
    assert len(content) > 100, "pocket.py content suspiciously short"

    denied = Path(project_root) / ".env"
    assert not is_read_allowed(str(denied)), ".env should be blocked"

check("/read loads allowed files + blocks denylist", test_read_command)


# ── Executor ──────────────────────────────────────────────────────────────────
skip("Executor", "requires interactive approval — tested manually")


# STAGE 4s — MODULE LIFECYCLE CONTRACT
# ═════════════════════════════════════════════════════════════════════════════

print("\n  Stage 4s — Lifecycle contract...\n")


# ── ABC enforcement ───────────────────────────────────────────────────────────
def test_abc_enforcement():
    from core.pocket_module import PocketModule

    # A class missing any of the four methods must not be instantiable
    class Incomplete(PocketModule):
        def start(self): pass
        def stop(self): pass
        # health_check and on_event intentionally missing

    try:
        Incomplete()
        raise AssertionError("TypeError not raised — ABC not enforcing contract")
    except TypeError:
        pass  # correct

check("ABC rejects incomplete module", test_abc_enforcement)

# --- 4r: Runtime State Manager ---
print("\n[4r] Runtime State Manager")
try:
    from core.state_manager import state

    # Expression
    state.set_expression("happy", source="test")
    assert state.expression == "happy"
    assert state.get("avatar", "expression_source") == "test"

    # WebSocket status
    state.set_websocket_status("CONNECTED")
    assert state.websocket_status == "CONNECTED"
    assert state.get("connection", "reconnect_attempts") == 0

    state.set_websocket_status("RECONNECTING")
    state.increment_reconnect_attempts()
    assert state.get("connection", "reconnect_attempts") == 1

    # Health
    state.update_health("ollama", True)
    state.update_health("chroma", True)
    state.update_health("piper", True)
    state.update_health("websocket", True)
    assert state.all_healthy()

    # Snapshot doesn't mutate live state
    snap = state.snapshot()
    snap["avatar"]["expression"] = "MUTATED"
    assert state.expression == "happy"

    # Invalid status raises
    try:
        state.set_websocket_status("BOGUS")
        print("  ❌ Should have raised ValueError")
    except ValueError:
        pass

    print("  ✅ State Manager — all checks passed")
    print(state)

except Exception as e:
    print(f"  ❌ State Manager failed: {e}")

    # --- 4q: Event Bus ---
print("\n[4q] Event Bus")
try:
    from core.event_bus import bus, event_bus_module

    received = []

    def handler_a(event):
        received.append(("a", event))

    def handler_b(event):
        received.append(("b", event))

    # Subscribe and emit
    bus.subscribe("test.event", handler_a)
    bus.subscribe("test.event", handler_b)
    bus.emit("test.event", {"value": 42})

    assert len(received) == 2, f"Expected 2 handlers called, got {len(received)}"
    assert received[0] == ("a", {"type": "test.event", "value": 42})
    assert received[1] == ("b", {"type": "test.event", "value": 42})

    # Unsubscribe
    bus.unsubscribe("test.event", handler_a)
    received.clear()
    bus.emit("test.event", {"value": 99})
    assert len(received) == 1, "handler_a should be gone"
    assert received[0][0] == "b"

    # Failing handler doesn't crash the bus
    def bad_handler(event):
        raise RuntimeError("intentional failure")

    bus.subscribe("test.event", bad_handler)
    received.clear()
    bus.emit("test.event", {})  # bad_handler fires, logs, handler_b still runs
    assert len(received) == 1, "handler_b should still run after bad_handler fails"

    # Emit with no subscribers doesn't crash
    bus.emit("event.with.no.subscribers", {"data": "ignored"})

    # Cleanup test subscriptions
    bus.unsubscribe_all("test.event")

    # Health check
    assert event_bus_module.health_check()

    print("  ✅ Event Bus — all checks passed")
    print(bus)

except Exception as e:
    print(f"  ❌ Event Bus failed: {e}")

    # --- 4n: WebSocket Reconnection Engine ---
print("\n[4n] WebSocket Reconnection Engine")
try:
    from core.websocket_server import websocket_module
    from core.state_manager import state
    from core.event_bus import bus

    events_received = []
    bus.subscribe("connection.websocket.connected",    lambda e: events_received.append(e["type"]))
    bus.subscribe("connection.websocket.disconnected", lambda e: events_received.append(e["type"]))
    bus.subscribe("connection.websocket.reconnecting", lambda e: events_received.append(e["type"]))
    bus.subscribe("connection.websocket.degraded",     lambda e: events_received.append(e["type"]))

    # Start — if Electron is running this will connect
    websocket_module.start()
    import time; time.sleep(1)

    ws_status = state.websocket_status
    print(f"  WebSocket status: {ws_status}")

    if ws_status == "CONNECTED":
        # Confirm send works
        sent = websocket_module.send({"command": "smoke_test_ping"})
        assert sent, "send() returned False despite CONNECTED status"
        print("  ✅ WebSocket reconnection engine — connected and send confirmed")
    else:
        # Electron not running — confirm degraded mode behavior (no crash)
        assert ws_status in ("DISCONNECTED", "RECONNECTING", "DEGRADED_MODE"), \
            f"Unexpected status: {ws_status}"
        # Confirm send silently drops without crashing
        sent = websocket_module.send({"command": "smoke_test_ping"})
        assert not sent, "send() should return False when not connected"
        print(f"  ✅ WebSocket reconnection engine — Electron not running, degraded gracefully ({ws_status})")

    # health_check reflects actual status
    healthy = websocket_module.health_check()
    assert healthy == (ws_status == "CONNECTED")

    # on_event ignores unknown events (already covered by on_event_safety test)

    # Cleanup test subscriptions
    bus.unsubscribe_all("connection.websocket.connected")
    bus.unsubscribe_all("connection.websocket.disconnected")
    bus.unsubscribe_all("connection.websocket.reconnecting")
    bus.unsubscribe_all("connection.websocket.degraded")

    print(f"  Events received during test: {events_received}")

except Exception as e:
    print(f"  ❌ WebSocket reconnection engine failed: {e}")

# --- 4i: Structured Logging ---
print("\n[4i] Structured Logging")
try:
    import json
    import os
    from core.logger import log, logger_module

    logger_module.start()
    assert logger_module.health_check(), "Logger health check failed"

    # Write one of each type
    log.command("echo smoke_test", approved=True, result="smoke_test")
    log.expression("happy", source="smoke_test")
    log.memory_retrieval(query="smoke test query", results=3)
    log.websocket("CONNECTED", attempt=0)
    log.error("smoke_test", "intentional test error entry")
    log.info("smoke_test", "4i smoke test complete")

    # Confirm entries landed in the file
    assert os.path.exists(log._log_path), "Log file not created"
    with open(log._log_path, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f.readlines() if l.strip()]

    assert len(lines) > 0, "Log file is empty"

    # Confirm last entry is valid JSON with required fields
    last = json.loads(lines[-1])
    assert "ts" in last, "Missing timestamp"
    assert "type" in last, "Missing type field"

    print(f"  Log file: {log._log_path}")
    print(f"  Entries in file: {len(lines)}")
    print("  ✅ Structured logging — all checks passed")

except Exception as e:
    print(f"  ❌ Structured logging failed: {e}")
    
# ── All module instances exist ────────────────────────────────────────────────
def test_module_instances():
    from core.pocket_module      import PocketModule
    from core.config_loader      import config_loader_module
    from core.backup_manager     import backup_manager_module
    from core.permissions        import permissions_module
    from core.avatar_router      import avatar_router_module
    from core.executor           import executor_module
    from core.event_bus          import event_bus_module
    from core.websocket_server   import websocket_module

    for mod in [
        config_loader_module,
        backup_manager_module,
        permissions_module,
        avatar_router_module,
        executor_module,
        event_bus_module,
        websocket_module,
    ]:
        assert isinstance(mod, PocketModule), f"{mod} is not a PocketModule"

check("All stateless module instances are PocketModule", test_module_instances)


# ── Stateless health checks ───────────────────────────────────────────────────
# These modules have no service dependencies — safe to check any time.

def test_health_config_loader():
    from core.config_loader import config_loader_module
    assert config_loader_module.health_check(), "config_loader health_check failed"

check("config_loader health_check", test_health_config_loader)


def test_health_backup_manager():
    from core.backup_manager import backup_manager_module
    backup_manager_module.start()  # ensures backup dir exists
    assert backup_manager_module.health_check(), "backup_manager health_check failed"

check("backup_manager health_check", test_health_backup_manager)


def test_health_permissions():
    from core.permissions import permissions_module
    permissions_module.start()  # ensures logs/ dir exists
    assert permissions_module.health_check(), "permissions health_check failed"

check("permissions health_check", test_health_permissions)


def test_health_avatar_router():
    from core.avatar_router import avatar_router_module
    assert avatar_router_module.health_check(), "avatar_router health_check — expressions.json may not have loaded"

check("avatar_router health_check", test_health_avatar_router)


def test_health_executor():
    from core.executor import executor_module
    assert executor_module.health_check(), "executor health_check — denylist may be empty in config.yaml"

check("executor health_check", test_health_executor)


# ── Service health checks (require running services) ─────────────────────────
# These call real services. They pass/fail based on what's currently running.

def test_health_memory():
    from core.memory import memory_module
    assert memory_module.health_check(), "memory health_check failed — is ChromaDB running?"

check("memory health_check (ChromaDB round-trip)", test_health_memory)


def test_health_llm():
    from core.llm import llm_module
    assert llm_module.health_check(), "llm health_check failed — is Ollama running?"

check("llm health_check (Ollama ping)", test_health_llm)


def test_health_tts():
    from core.tts import tts_module
    assert tts_module.health_check(), "tts health_check failed — Piper exe not found"

check("tts health_check (Piper exe exists)", test_health_tts)


def test_health_stt():
    from core.stt import stt_module
    stt_module.start()  # loads Whisper model
    assert stt_module.health_check(), "stt health_check failed — Whisper model did not load"

check("stt health_check (Whisper model loads)", test_health_stt)


def test_health_websocket():
    from core.websocket_server import websocket_module
    websocket_module.start()
    import time; time.sleep(1)  # give the connection a moment
    assert websocket_module.health_check(), "websocket health_check failed — is Electron avatar running?"

check("websocket health_check (avatar connected)", test_health_websocket)


# ── on_event ignores unknown events ──────────────────────────────────────────
def test_on_event_safety():
    from core.config_loader  import config_loader_module
    from core.backup_manager import backup_manager_module
    from core.permissions    import permissions_module
    from core.avatar_router  import avatar_router_module
    from core.executor       import executor_module
    from core.memory         import memory_module
    from core.llm            import llm_module
    from core.tts            import tts_module
    from core.stt            import stt_module
    from core.event_bus      import event_bus_module
    from core.websocket_server import websocket_module

    garbage_event = {"type": "totally.unknown.event", "payload": "nonsense"}

    for mod in [
        config_loader_module, backup_manager_module, permissions_module,
        avatar_router_module, executor_module, memory_module,
        llm_module, tts_module, stt_module, event_bus_module, websocket_module
    ]:
        mod.on_event(garbage_event)  # must not raise

check("on_event silently ignores unknown events (all modules)", test_on_event_safety)


# ═════════════════════════════════════════════════════════════════════════════
# SUMMARY
# ═════════════════════════════════════════════════════════════════════════════

passed  = sum(1 for r in results if r[0] == PASS)
failed  = sum(1 for r in results if r[0] == FAIL)
skipped = sum(1 for r in results if r[0] == SKIP)

print(f"\n  {passed} passed · {failed} failed · {skipped} skipped")

if failed == 0:
    print("  System's are good to go, boss.\n")
else:
    print("  Shit has hit the fan.\n")
    sys.exit(1)
