import whisper
import sounddevice as sd
import soundfile as sf
import numpy as np
import requests
import subprocess
import tempfile
import os
import sys
import json
import re
from pathlib import Path
from pynput import keyboard

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
OLLAMA_URL      = "http://localhost:11434/api/chat"
MEMORY_API_URL  = "http://localhost:5000/remember"
MEMORY_HEALTH   = "http://localhost:5000/health"
MODEL           = "llama3.1"
WHISPER_MODEL   = "base"
SAMPLE_RATE     = 16000
PUSH_TO_TALK    = keyboard.Key.f9

PIPER_EXE       = r"piper\piper.exe"
PIPER_VOICE     = r"piper\voices\en_US-lessac-medium.onnx"
PIPER_CONFIG    = r"piper\voices\en_US-lessac-medium.onnx.json"

# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------
recording       = False
audio_chunks    = []
session_history = []
stream          = None

# ---------------------------------------------------------------------------
# Memory API helpers
# ---------------------------------------------------------------------------

def check_memory_api() -> bool:
    """Check if the memory API in the Docker container is reachable."""
    try:
        r = requests.get(MEMORY_HEALTH, timeout=2)
        data = r.json()
        print(f"  [Memory API connected — {data.get('memories', '?')} memories stored]")
        return True
    except Exception:
        print("  [Memory API not reachable — voice sessions won't persist to memory]")
        print("  [Make sure Docker containers are running and port 5000 is mapped]")
        return False


def persist_memory(role: str, content: str):
    """Send a memory entry to the Docker container's ChromaDB via the API."""
    try:
        requests.post(
            MEMORY_API_URL,
            json={"role": role, "content": content},
            timeout=5
        )
    except Exception:
        pass  # silently fail — don't interrupt the conversation


# ---------------------------------------------------------------------------
# Load Whisper
# ---------------------------------------------------------------------------

print("\n🦦 Pocket Voice — Loading Whisper model...")
stt_model = whisper.load_model(WHISPER_MODEL)
print(f"   Whisper '{WHISPER_MODEL}' ready")

# Check memory API connection
memory_available = check_memory_api()

print(f"\n   Hold {PUSH_TO_TALK} to talk, release to send")
print(f"   Press Ctrl+C to quit\n")


# ---------------------------------------------------------------------------
# Recording
# ---------------------------------------------------------------------------

def start_recording():
    global recording, audio_chunks, stream
    audio_chunks = []
    recording    = True
    print("🎙️  Listening...", end="", flush=True)

    def callback(indata, frames, time, status):
        if recording:
            audio_chunks.append(indata.copy())

    stream = sd.InputStream(samplerate=SAMPLE_RATE, channels=1,
                            dtype="float32", callback=callback)
    stream.start()


def stop_recording() -> np.ndarray | None:
    global recording, stream
    recording = False
    stream.stop()
    stream.close()
    print(" done")

    if not audio_chunks:
        return None

    audio    = np.concatenate(audio_chunks, axis=0).flatten()
    duration = len(audio) / SAMPLE_RATE

    if duration < 0.5:
        print("   (too short — ignored)")
        return None

    return audio


# ---------------------------------------------------------------------------
# Transcription
# ---------------------------------------------------------------------------

def transcribe(audio: np.ndarray) -> str:
    print("   Transcribing...", end="", flush=True)
    result = stt_model.transcribe(audio, fp16=False, language="en")
    text   = result["text"].strip()
    print(f' "{text}"')
    return text


# ---------------------------------------------------------------------------
# Ollama
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are Pocket, a personal AI assistant and companion for the user.
You have persistent memory and remember past conversations.
You are currently in voice mode — keep responses conversational and concise.
Avoid markdown, bullet points, and code blocks since responses will be spoken aloud.
Speak naturally — like a knowledgeable friend having a conversation.
Be warm, direct, and don't over-explain."""


def ask_pocket(user_text: str) -> str:
    global session_history

    session_history.append({"role": "user", "content": user_text})

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + session_history

    print("   Thinking...", end="", flush=True)

    try:
        response = requests.post(OLLAMA_URL, json={
            "model":    MODEL,
            "messages": messages,
            "stream":   False
        }, timeout=60)

        data  = response.json()
        reply = data.get("message", {}).get("content", "")

        if not reply:
            reply = data.get("response", "Sorry, I didn't catch that.")

        session_history.append({"role": "assistant", "content": reply})
        print(" done")
        return reply

    except requests.exceptions.Timeout:
        return "Sorry, that took too long. Try again."
    except Exception as e:
        return f"Error reaching Ollama: {e}"


# ---------------------------------------------------------------------------
# Text to speech
# ---------------------------------------------------------------------------

def clean_for_speech(text: str) -> str:
    """Strip anything that sounds weird when spoken aloud."""
    text = re.sub(r"#{1,6}\s*",          "",    text)   # headers
    text = re.sub(r"\*{1,2}(.+?)\*{1,2}", r"\1", text)  # bold/italic
    text = re.sub(r"`{1,3}[^`]*`{1,3}",  "",    text)   # code
    text = re.sub(r"\[(.+?)\]\(.+?\)",   r"\1", text)   # links
    text = re.sub(r"[-•]\s+",            "",    text)   # bullets
    text = re.sub(r"\n{2,}",             ". ",  text)   # double newlines
    text = re.sub(r"\n",                 " ",   text)   # single newlines
    text = re.sub(r"\s{2,}",             " ",   text)   # extra spaces
    return text.strip()


def speak(text: str):
    clean = clean_for_speech(text)
    print(f"\nPocket: {clean}\n")

    if not Path(PIPER_EXE).exists():
        print("   [Piper not found — text only mode]")
        return

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name

        proc = subprocess.run(
            [PIPER_EXE, "--model",       PIPER_VOICE,
                        "--config",      PIPER_CONFIG,
                        "--output_file", tmp_path],
            input=clean.encode("utf-8"),
            capture_output=True
        )

        if proc.returncode == 0 and Path(tmp_path).exists():
            data, samplerate = sf.read(tmp_path)
            sd.play(data, samplerate)
            sd.wait()
        else:
            print(f"   [Piper error: {proc.stderr.decode()}]")

    except Exception as e:
        print(f"   [TTS error: {e}]")
    finally:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Full exchange — transcribe → ask → speak → remember
# ---------------------------------------------------------------------------

def handle_exchange(audio: np.ndarray):
    text = transcribe(audio)
    if not text:
        return

    reply = ask_pocket(text)
    speak(reply)

    # Persist both sides to ChromaDB via the memory API
    if memory_available:
        persist_memory("user",      f"[voice] {text}")
        persist_memory("assistant", f"[voice] {reply}")


# ---------------------------------------------------------------------------
# Hotkey handling
# ---------------------------------------------------------------------------

def on_press(key):
    global recording
    if key == PUSH_TO_TALK and not recording:
        start_recording()


def on_release(key):
    if key == PUSH_TO_TALK and recording:
        audio = stop_recording()
        if audio is not None:
            handle_exchange(audio)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    try:
        with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
            listener.join()
    except KeyboardInterrupt:
        print("\n\n🦦 Pocket Voice signing off. Later.\n")
        sys.exit(0)
