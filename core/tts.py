# core/tts.py
# Piper TTS — audio synthesis and playback queue.
#
# Public API:
#   tts_queue      — put(text) to enqueue speech; put(None) to stop worker
#   speaking_flag  — threading.Event, set while audio is playing
#   run_piper_tts(text)  — synthesise + play one utterance (blocking)
#   tts_worker()         — background thread target; drains tts_queue
#
# Stage 4s: TTSModule implements PocketModule.
#   start()        — launches the background tts_worker thread
#   stop()         — sends None sentinel to drain and exit the worker thread
#   health_check() — verifies Piper executable exists on disk
#   on_event()     — handles "tts.speak" events from the bus (4q)

import os
import re
import queue
import threading

import numpy as np
import sounddevice as sd

from core.config_loader import CFG
from core.pocket_module import PocketModule
from core.degradation import mark_degraded, mark_recovered

# ── Path constants ────────────────────────────────────────────────────────────
PIPER_EXE    = CFG["tts"]["piper_exe_abs"]
PIPER_MODEL  = CFG["tts"]["piper_model_abs"]
PIPER_CONFIG = CFG["tts"]["piper_config_abs"]

# ── Shared state ──────────────────────────────────────────────────────────────
tts_queue     = queue.Queue()
speaking_flag = threading.Event()
_worker_thread: threading.Thread | None = None


# ═════════════════════════════════════════════════════════════════════════════
# CORE FUNCTIONS (unchanged public API)
# ═════════════════════════════════════════════════════════════════════════════

def run_piper_tts(text: str):
    """Synthesise *text* with Piper and play it through the default output device.

    Blocks until playback is complete. Sets/clears *speaking_flag* around
    playback so other subsystems can check whether audio is active.
    """
    import subprocess

    if not os.path.exists(PIPER_EXE):
        mark_degraded("piper", f"Piper executable not found: {PIPER_EXE}")
        return

    clean = re.sub(r"[*_`#>\-]", "", text)
    clean = re.sub(r"\s+", " ", clean).strip()
    if not clean:
        return

    try:
        speaking_flag.set()
        proc = subprocess.Popen(
            [PIPER_EXE, "--model", PIPER_MODEL, "--output-raw"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        raw_audio, _ = proc.communicate(input=clean.encode("utf-8"))
        audio_array  = np.frombuffer(raw_audio, dtype=np.int16).astype(np.float32) / 32768.0
        sd.play(audio_array, samplerate=22050)
        sd.wait()
        mark_recovered("piper")  # no-op unless Piper had been down
    except Exception as e:
        mark_degraded("piper", str(e))
    finally:
        speaking_flag.clear()


def tts_worker():
    """Background thread target — drains *tts_queue* one utterance at a time.

    Send ``None`` to the queue to shut the worker down gracefully.
    """
    while True:
        text = tts_queue.get()
        if text is None:
            break
        run_piper_tts(text)
        tts_queue.task_done()


# ═════════════════════════════════════════════════════════════════════════════
# LIFECYCLE — Stage 4s
# ═════════════════════════════════════════════════════════════════════════════

class TTSModule(PocketModule):
    """Lifecycle wrapper for Piper TTS.

    start()        — spins up the tts_worker daemon thread.
    stop()         — sends the None sentinel; worker drains the queue and exits.
    health_check() — verifies the Piper executable exists on disk.
    on_event()     — handles "tts.speak" events so other modules can enqueue
                     speech without importing this module directly.
    """

    def start(self) -> None:
        global _worker_thread
        _worker_thread = threading.Thread(target=tts_worker, daemon=True, name="tts-worker")
        _worker_thread.start()

    def stop(self) -> None:
        # None is the sentinel that tells tts_worker to exit after draining.
        tts_queue.put(None)
        if _worker_thread and _worker_thread.is_alive():
            _worker_thread.join(timeout=5)

    def health_check(self) -> bool:
        try:
            return os.path.exists(PIPER_EXE)
        except Exception as e:
            print(f"  [TTSModule] health_check error: {e}")
            return False

    def on_event(self, event: dict) -> None:
        # Supported event: {"type": "tts.speak", "text": "...", "priority": 1}
        # Priority is reserved for 4q — currently all speech is FIFO.
        if event.get("type") != "tts.speak":
            return
        text = event.get("text", "")
        if text:
            tts_queue.put(text)


tts_module = TTSModule()
