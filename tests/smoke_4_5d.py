# tests/smoke_4_5d.py
# Stage 4.5d verification — mutex serialization + Piper timeout recovery.
# Run: python -m tests.smoke_4_5d   (from project root, venv active)

import subprocess
import threading
import time
from unittest.mock import patch

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import core.llm as llm
import core.tts as tts
import core.orchestrator as orchestrator

def test_mutex_serializes():
    """5 concurrent turns must run one-at-a-time and leave history uncorrupted."""
    orchestrator.session_history.clear()

    concurrency = {"now": 0, "max": 0}
    guard = threading.Lock()

    def fake_chat(messages, options=None):
        with guard:
            concurrency["now"] += 1
            concurrency["max"] = max(concurrency["max"], concurrency["now"])
        time.sleep(0.3)  # stand in for a real Ollama call
        with guard:
            concurrency["now"] -= 1
        return "ok"

    with patch("core.orchestrator.chat", side_effect=fake_chat), \
         patch.object(orchestrator.websocket_module, "send"), \
         patch("core.orchestrator.save_memory"), \
         patch("core.orchestrator.get_relevant_memories", return_value=""), \
         patch("core.orchestrator.tts_queue"):
        threads = [
            threading.Thread(target=llm.handle_user_input_sync, args=(f"msg {i}",))
            for i in range(5)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

    assert concurrency["max"] == 1, f"turns overlapped: max concurrency = {concurrency['max']}"
    assert len(orchestrator.session_history) == 10, f"expected 10 history entries, got {len(orchestrator.session_history)}"
    orchestrator.session_history.clear()
    print("PASS mutex — 5 concurrent turns serialized (max concurrency 1), history intact")


def test_piper_timeout_returns_cleanly():
    """A hung synth must time out, mark degraded, and clear speaking_flag — not raise."""
    class HangProc:
        def communicate(self, input=None, timeout=None):
            raise subprocess.TimeoutExpired("piper", timeout)
        def kill(self):
            pass

    tts.speaking_flag.clear()
    with patch("os.path.exists", return_value=True), \
         patch("subprocess.Popen", return_value=HangProc()), \
         patch("core.tts.mark_degraded") as md:
        tts.run_piper_tts("this utterance hangs forever")  # must return, not raise

    assert not tts.speaking_flag.is_set(), "speaking_flag stuck set after a timeout"
    assert md.called, "timeout did not mark piper degraded"
    print("PASS piper-timeout — hung synth skipped, flag cleared, degraded marked")


def test_piper_worker_recovers_after_hang():
    """The worker must survive a hung utterance and still play the next one."""
    played = []

    class HangProc:
        def communicate(self, input=None, timeout=None):
            raise subprocess.TimeoutExpired("piper", timeout)
        def kill(self):
            pass

    class GoodProc:
        def communicate(self, input=None, timeout=None):
            return (b"\x00\x00" * 16, b"")  # tiny valid int16 buffer
        def kill(self):
            pass

    seq = [HangProc(), GoodProc()]

    with patch("os.path.exists", return_value=True), \
         patch("subprocess.Popen", side_effect=lambda *a, **k: seq.pop(0)), \
         patch("core.tts.sd.play", lambda *a, **k: played.append(True)), \
         patch("core.tts.sd.wait", lambda *a, **k: None), \
         patch("core.tts.mark_degraded"), \
         patch("core.tts.mark_recovered"):
        worker = threading.Thread(target=tts.tts_worker, daemon=True)
        worker.start()
        tts.tts_queue.put("will hang")
        tts.tts_queue.put("should still play")
        tts.tts_queue.join()      # both processed — join BEFORE the sentinel
        tts.tts_queue.put(None)   # stop the worker

    assert played, "second utterance never played — worker wedged on the hang"
    print("PASS piper-worker — worker survived a hung utterance and played the next")


if __name__ == "__main__":
    test_mutex_serializes()
    test_piper_timeout_returns_cleanly()
    test_piper_worker_recovers_after_hang()
    print("\nAll scripted 4.5d checks passed.")