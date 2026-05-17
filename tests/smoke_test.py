# tests/smoke_test.py
# Stage 4a.1 — Smoke test suite
#
# Confirms all core systems are alive after any change.
# Run before and after significant changes:
#   python tests/smoke_test.py
#
# Does NOT test /read or executor — those features aren't built yet.
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

    # Clean up
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

    # Play it so we can confirm audibly too
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
# ── Skipped (not built yet) ───────────────────────────────────────────────────
skip("/read command", "not built yet — Stage 4f")
skip("Executor", "not built yet — Stage 4g")


# ═════════════════════════════════════════════════════════════════════════════
# SUMMARY
# ═════════════════════════════════════════════════════════════════════════════

passed = sum(1 for r in results if r[0] == PASS)
failed = sum(1 for r in results if r[0] == FAIL)
skipped = sum(1 for r in results if r[0] == SKIP)

print(f"\n  {passed} passed · {failed} failed · {skipped} skipped")

if failed == 0:
    print("  All systems nominal.\n")
else:
    print("  Some systems need attention.\n")
    sys.exit(1)
