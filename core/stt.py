# core/stt.py
# Whisper STT — recording, transcription, voice input handler, F9 keyboard listener.
#
# Public API:
#   recording_flag          — threading.Event, set while mic is active
#   init_whisper()          — load Whisper model (call once at startup)
#   record_until_silence()  — capture audio until silence/timeout, return ndarray
#   transcribe_audio(audio) — transcribe ndarray → str
#   handle_voice_input(on_input) — full record→transcribe→callback pipeline
#   keyboard_listener(on_input)  — F9 push-to-talk listener (blocking, run in thread)

import threading
import time

import numpy as np
import sounddevice as sd

from config.settings import (
    WHISPER_MODEL,
    SAMPLE_RATE,
    CHANNELS,
    SILENCE_THRESHOLD,
    SILENCE_DURATION,
    MAX_RECORD_SECS,
)
from core.tts import speaking_flag

# ── Optional Whisper import ───────────────────────────────────────────────────
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

# ── Shared state ──────────────────────────────────────────────────────────────
recording_flag = threading.Event()
_whisper_model = None


# ═════════════════════════════════════════════════════════════════════════════
# INIT
# ═════════════════════════════════════════════════════════════════════════════

def init_whisper():
    """Load the Whisper model. Call once at startup before any transcription."""
    global _whisper_model
    if not WHISPER_AVAILABLE:
        return
    try:
        _whisper_model = whisper.load_model(WHISPER_MODEL)
        print(f"  Loading Whisper model... '{WHISPER_MODEL}' ready ✓")
    except Exception as e:
        print(f"  [Whisper load failed: {e}]")


# ═════════════════════════════════════════════════════════════════════════════
# STT
# ═════════════════════════════════════════════════════════════════════════════

def record_until_silence() -> np.ndarray | None:
    """Record audio until silence is detected or max duration reached."""
    frames        = []
    silent_chunks = 0
    chunks_per_sec  = int(SAMPLE_RATE / 1024)
    silence_chunks  = int(SILENCE_DURATION * chunks_per_sec)

    with sd.InputStream(
        samplerate=SAMPLE_RATE, channels=CHANNELS,
        dtype="float32", blocksize=1024
    ) as stream:
        start_time = time.time()
        while recording_flag.is_set():
            if time.time() - start_time > MAX_RECORD_SECS:
                break
            chunk, _ = stream.read(1024)
            frames.append(chunk.copy())
            if np.max(np.abs(chunk)) < SILENCE_THRESHOLD:
                silent_chunks += 1
                if silent_chunks >= silence_chunks and len(frames) > chunks_per_sec:
                    break
            else:
                silent_chunks = 0

    if not frames:
        return None
    return np.concatenate(frames, axis=0).flatten()


def transcribe_audio(audio: np.ndarray) -> str:
    """Transcribe a float32 audio array to text via Whisper."""
    if _whisper_model is None:
        return ""
    try:
        result = _whisper_model.transcribe(audio, fp16=False, language="en")
        return result["text"].strip()
    except Exception as e:
        print(f"  [Transcription error: {e}]")
        return ""


def handle_voice_input(on_input):
    """Record → transcribe → call on_input(text).

    *on_input* is a callable (e.g. handle_user_input_sync from pocket.py)
    passed in to avoid a circular import.
    """
    recording_flag.set()
    audio = record_until_silence()
    recording_flag.clear()
    if audio is None or len(audio) < SAMPLE_RATE * 0.3:
        return
    text = transcribe_audio(audio)
    if text:
        print(f'You (voice): "{text}"')
        on_input(text)


# ═════════════════════════════════════════════════════════════════════════════
# KEYBOARD — F9 push-to-talk
# ═════════════════════════════════════════════════════════════════════════════

def keyboard_listener(on_input):
    """Block and listen for F9 push-to-talk. Run in a daemon thread.

    *on_input* is passed through to handle_voice_input.
    """
    from pynput import keyboard

    f9_held = False

    def on_press(key):
        nonlocal f9_held
        if key == keyboard.Key.f9 and not f9_held and not speaking_flag.is_set():
            f9_held = True
            t = threading.Thread(
                target=handle_voice_input, args=(on_input,), daemon=True
            )
            t.start()

    def on_release(key):
        nonlocal f9_held
        if key == keyboard.Key.f9:
            f9_held = False
            recording_flag.clear()

    try:
        with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
            listener.join()
    except Exception as e:
        print(f"  [Keyboard listener error: {e}]")
