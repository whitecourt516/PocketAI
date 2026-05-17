# core/tts.py
# Piper TTS — audio synthesis and playback queue.
#
# Public API:
#   tts_queue      — put(text) to enqueue speech; put(None) to stop worker
#   speaking_flag  — threading.Event, set while audio is playing
#   run_piper_tts(text)  — synthesise + play one utterance (blocking)
#   tts_worker()         — background thread target; drains tts_queue

import os
import re
import queue
import threading

import numpy as np
import sounddevice as sd

# ── Path constants ────────────────────────────────────────────────────────────
# Derived at import time from this file's location (core/ → project root).
_core_dir    = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.join(_core_dir, '..')

PIPER_EXE    = os.path.join(_project_root, "piper", "piper.exe")
PIPER_MODEL  = os.path.join(_project_root, "piper", "voices", "en_US-lessac-medium.onnx")
PIPER_CONFIG = os.path.join(_project_root, "piper", "voices", "en_US-lessac-medium.onnx.json")

# ── Shared state ──────────────────────────────────────────────────────────────
tts_queue     = queue.Queue()
speaking_flag = threading.Event()


# ═════════════════════════════════════════════════════════════════════════════
# TTS
# ═════════════════════════════════════════════════════════════════════════════

def run_piper_tts(text: str):
    """Synthesise *text* with Piper and play it through the default output device.

    Blocks until playback is complete.  Sets/clears *speaking_flag* around
    playback so other subsystems can check whether audio is active.
    """
    import subprocess  # local — only needed when Piper is present

    if not os.path.exists(PIPER_EXE):
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
    except Exception as e:
        print(f"  [TTS error: {e}]")
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
