"""
pocket.py — Pocket Unified Engine
───────────────────────────────────────────────────────────────────────────────
Single script that handles:
  - Push-to-talk voice input (F9) via Whisper
  - Text input fallback via CLI
  - Ollama LLM with session history
  - ChromaDB memory persistence (direct — no HTTP middleman)
  - Piper TTS voice output
  - Avatar expression control via WebSocket
  - Output panel for long/code responses

HOW TO RUN:
  python pocket.py

REQUIREMENTS:
  pip install chromadb ollama whisper sounddevice numpy websockets pynput
"""

import asyncio
import json
import os
import re
import subprocess
import sys
import threading
import time
import uuid
import queue

import numpy as np
import sounddevice as sd
import websockets

from pathlib import Path
from pynput import keyboard

# ── Path setup ────────────────────────────────────────────────────────────────
script_dir   = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(script_dir, '..', '..')
sys.path.insert(0, project_root)

# ── Project imports ───────────────────────────────────────────────────────────
from config.settings import (
    MODEL, COLLECTION_NAME, N_MEMORIES, KNOWLEDGE_FILES,
    WHISPER_MODEL, SAMPLE_RATE, CHANNELS,
    SILENCE_THRESHOLD, SILENCE_DURATION, MAX_RECORD_SECS,
    WEBSOCKET_PORT, TYPING_CHARS_PER_SEC,
)
from config.persona import SYSTEM_PROMPT

import chromadb
import ollama

# ── Optional imports ──────────────────────────────────────────────────────────
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

try:
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False

# ── Path constants (runtime-derived, stay here not in config/) ────────────────
PIPER_EXE    = os.path.join(project_root, "piper", "piper.exe")
PIPER_MODEL  = os.path.join(project_root, "piper", "voices", "en_US-lessac-medium.onnx")
PIPER_CONFIG = os.path.join(project_root, "piper", "voices", "en_US-lessac-medium.onnx.json")
CHROMA_PATH  = os.path.join(project_root, "chroma_data")
AVATAR_WS_URL = "ws://localhost:3000"

MAX_SUBTITLE_LEN = 120

# ── Runtime clients ───────────────────────────────────────────────────────────
ollama_client = ollama.Client(host=os.getenv("OLLAMA_HOST", "http://localhost:11434"))
chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
memory        = chroma_client.get_or_create_collection(name=COLLECTION_NAME)

# ── Runtime state ─────────────────────────────────────────────────────────────
session_history = []
tts_queue       = queue.Queue()
ws_clients      = set()
speaking_flag   = threading.Event()
recording_flag  = threading.Event()
f9_held         = False

# ── Whisper init ──────────────────────────────────────────────────────────────
whisper_model = None
if WHISPER_AVAILABLE:
    try:
        whisper_model = whisper.load_model(WHISPER_MODEL)
        print(f"  Loading Whisper model... '{WHISPER_MODEL}' ready ✓")
    except Exception as e:
        print(f"  [Whisper load failed: {e}]")

# ── Expression engine ─────────────────────────────────────────────────────────
try:
    from expression_engine import ExpressionEngine
    expression_engine = ExpressionEngine()
    EXPRESSION_ENGINE_AVAILABLE = True
except ImportError:
    expression_engine = None
    EXPRESSION_ENGINE_AVAILABLE = False


# ═════════════════════════════════════════════════════════════════════════════
# MEMORY  (ChromaDB — direct, no HTTP)
# ═════════════════════════════════════════════════════════════════════════════

def save_memory(role: str, content: str):
    """Persist a message to ChromaDB. Skips short throwaway content."""
    if len(content.strip()) < 20:
        return
    memory.add(
        documents=[f"{role}: {content}"],
        ids=[str(uuid.uuid4())],
        metadatas=[{"role": role, "timestamp": str(time.time())}]
    )


def get_relevant_memories(query: str) -> str:
    """Retrieve the most relevant past memories for the current query."""
    try:
        results = memory.query(query_texts=[query], n_results=N_MEMORIES)
        if not results["documents"][0]:
            return ""
        mems = "\n".join(results["documents"][0])
        return f"--- Relevant memories ---\n{mems}\n---"
    except Exception:
        return ""


def load_knowledge_file(filepath: str):
    """Chunk and seed a text/markdown file into ChromaDB."""
    path = os.path.join(project_root, filepath) if not os.path.isabs(filepath) else filepath
    if not os.path.exists(path):
        print(f"  [Knowledge file not found: {path}]")
        return
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    chunk_size, overlap = 600, 80
    chunks, start = [], 0
    while start < len(content):
        chunks.append(content[start:start + chunk_size])
        start += chunk_size - overlap
    for chunk in chunks:
        if chunk.strip():
            save_memory("knowledge", chunk)
    print(f"  [Knowledge loaded: {os.path.basename(path)} ({len(chunks)} chunks)]")


def bootstrap_knowledge():
    """Seed knowledge files on first run only."""
    try:
        existing = memory.get(where={"role": "knowledge"}, limit=1)
        if existing["ids"]:
            return
    except Exception:
        pass
    print("\n  [First run — loading knowledge files...]")
    for f in KNOWLEDGE_FILES:
        load_knowledge_file(f)
    print()


# ═════════════════════════════════════════════════════════════════════════════
# AVATAR — WebSocket connection to Electron
# ═════════════════════════════════════════════════════════════════════════════

_avatar_ws        = None
_avatar_connected = False
_loop             = None


async def _avatar_connect():
    global _avatar_ws, _avatar_connected
    try:
        _avatar_ws = await websockets.connect(AVATAR_WS_URL)
        _avatar_connected = True
        print("  [Avatar connected ✓]")
    except Exception as e:
        _avatar_connected = False
        print(f"  [Avatar not connected — running without avatar]")


async def _avatar_send(msg: dict):
    global _avatar_ws, _avatar_connected
    if not _avatar_connected or not _avatar_ws:
        return
    try:
        await _avatar_ws.send(json.dumps(msg))
    except Exception:
        _avatar_connected = False


def avatar_send(msg: dict):
    """Thread-safe fire-and-forget send to avatar."""
    if _loop and _avatar_connected:
        asyncio.run_coroutine_threadsafe(_avatar_send(msg), _loop)


def avatar_expression(name: str):
    avatar_send({"type": "expression", "value": name})


def avatar_subtitle(text: str, duration: int = 5000):
    avatar_send({"type": "speech", "text": text, "duration": duration})


def avatar_panel(content: str, content_type: str, title: str = "Pocket"):
    avatar_send({"type": "panel", "content": content,
                 "contentType": content_type, "title": title})


def avatar_panel_close():
    avatar_send({"type": "panel_close"})


def avatar_thinking():
    avatar_expression("thinking")
    avatar_send({"type": "wander_pause"})


def avatar_done_thinking():
    avatar_send({"type": "wander_resume"})


def _run_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()


def start_avatar_connection():
    global _loop
    _loop = asyncio.new_event_loop()
    t = threading.Thread(target=_run_loop, args=(_loop,), daemon=True)
    t.start()
    asyncio.run_coroutine_threadsafe(_avatar_connect(), _loop)


# ═════════════════════════════════════════════════════════════════════════════
# EMOTION / CONTENT DETECTION
# ═════════════════════════════════════════════════════════════════════════════

EMOTION_RULES = [
    ("excited",   ["great news", "excellent", "perfect", "amazing", "fantastic",
                   "absolutely", "wonderful", "love it", "let's go", "ready"]),
    ("happy",     ["sure", "happy to", "of course", "glad", "here you go",
                   "done", "finished", "complete", "success", "worked"]),
    ("thinking",  ["let me think", "hmm", "considering", "analyzing",
                   "let me check", "working on", "calculating"]),
    ("surprised", ["oh", "interesting", "unexpected", "wow", "actually",
                   "wait", "huh", "that's new"]),
    ("concerned", ["error", "problem", "issue", "failed", "warning", "careful",
                   "incorrect", "wrong", "cannot", "unable", "sorry"]),
    ("sleepy",    ["winding down", "quiet", "slow", "rest", "later", "tired"]),
    ("smug",      ["as i expected", "told you", "obvious", "clearly",
                   "naturally", "as predicted"]),
    ("sad",       ["unfortunately", "sadly", "regret", "can't",
                   "not possible", "impossible"]),
]


def detect_emotion(text: str) -> str:
    lower = text.lower()
    for emotion, keywords in EMOTION_RULES:
        if any(kw in lower for kw in keywords):
            return emotion
    return "neutral"


def detect_content_type(text: str) -> str:
    if "```" in text:
        return "code"
    if len(text) > MAX_SUBTITLE_LEN and (
        "#" in text or "\n-" in text or "\n*" in text
    ):
        return "markdown"
    if len(text) > MAX_SUBTITLE_LEN:
        return "text"
    return "subtitle"


def extract_code(text: str) -> str:
    matches = re.findall(r"```(?:\w+)?\n?(.*?)```", text, re.DOTALL)
    return "\n\n".join(m.strip() for m in matches) if matches else text


def truncate_subtitle(text: str) -> str:
    text = text.strip()
    if len(text) <= MAX_SUBTITLE_LEN:
        return text
    return text[:MAX_SUBTITLE_LEN].rsplit(' ', 1)[0] + "…"


def send_to_avatar(response_text: str):
    """Route Pocket's reply to the avatar — expression + subtitle or panel."""
    emotion      = detect_emotion(response_text)
    content_type = detect_content_type(response_text)

    avatar_expression(emotion)

    if content_type == "subtitle":
        duration = max(3000, len(response_text) * 60)
        avatar_subtitle(response_text, duration)
        avatar_panel_close()
    elif content_type == "code":
        code = extract_code(response_text)
        avatar_subtitle("Here's the code ↘", 3000)
        avatar_panel(code, "code", "Code")
    else:
        first = response_text.split('.')[0].strip() + '.'
        avatar_subtitle(truncate_subtitle(first), 4000)
        avatar_panel(response_text, content_type, "Pocket")

    avatar_done_thinking()


# ═════════════════════════════════════════════════════════════════════════════
# TTS — Piper
# ═════════════════════════════════════════════════════════════════════════════

def run_piper_tts(text: str):
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
    """Consume TTS queue in a background thread."""
    while True:
        text = tts_queue.get()
        if text is None:
            break
        run_piper_tts(text)
        tts_queue.task_done()


# ═════════════════════════════════════════════════════════════════════════════
# STT — Whisper
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
    if whisper_model is None:
        return ""
    try:
        result = whisper_model.transcribe(audio, fp16=False, language="en")
        return result["text"].strip()
    except Exception as e:
        print(f"  [Transcription error: {e}]")
        return ""


def handle_voice_input():
    recording_flag.set()
    audio = record_until_silence()
    recording_flag.clear()
    if audio is None or len(audio) < SAMPLE_RATE * 0.3:
        return
    text = transcribe_audio(audio)
    if text:
        print(f'You (voice): "{text}"')
        handle_user_input_sync(text)


# ═════════════════════════════════════════════════════════════════════════════
# LLM — Ollama chat
# ═════════════════════════════════════════════════════════════════════════════

def handle_user_input_sync(text: str):
    """Process user input, get LLM reply, update memory and avatar."""
    global session_history

    avatar_thinking()

    past        = get_relevant_memories(text)
    full_system = SYSTEM_PROMPT + (f"\n\n{past}" if past else "")

    messages = [{"role": "system", "content": full_system}]
    messages += session_history
    messages.append({"role": "user", "content": text})

    try:
        response = ollama_client.chat(model=MODEL, messages=messages)
        reply    = response["message"]["content"]
    except Exception as e:
        reply = f"[LLM error: {e}]"
        print(reply)
        avatar_done_thinking()
        return

    session_history.append({"role": "user",      "content": text})
    session_history.append({"role": "assistant",  "content": reply})

    save_memory("user",      text)
    save_memory("assistant", reply)

    print(f"\nPocket: {reply}\n")

    send_to_avatar(reply)
    tts_queue.put(reply)


# ═════════════════════════════════════════════════════════════════════════════
# KEYBOARD — F9 push-to-talk
# ═════════════════════════════════════════════════════════════════════════════

def keyboard_listener():
    global f9_held

    def on_press(key):
        global f9_held
        if key == keyboard.Key.f9 and not f9_held and not speaking_flag.is_set():
            f9_held = True
            t = threading.Thread(target=handle_voice_input, daemon=True)
            t.start()

    def on_release(key):
        global f9_held
        if key == keyboard.Key.f9:
            f9_held = False
            recording_flag.clear()

    try:
        with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
            listener.join()
    except Exception as e:
        print(f"  [Keyboard listener error: {e}]")


# ═════════════════════════════════════════════════════════════════════════════
# CLI — text input loop
# ═════════════════════════════════════════════════════════════════════════════

def cli_input_loop():
    print("\nType a message or hold F9 to speak.")
    print("Commands: /quit  /clear  /memory  /load <file>\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  [Pocket signing off. Later user.]\n")
            os._exit(0)

        if not user_input:
            continue

        if user_input.lower() in ("/quit", "quit", "exit", "bye"):
            print("\n  [Pocket signing off. Later user.]\n")
            os._exit(0)

        if user_input.lower() == "/clear":
            session_history.clear()
            print("  [Session cleared]\n")
            continue

        if user_input.lower() == "/memory":
            print(f"  [Memory: {memory.count()} entries in ChromaDB]\n")
            continue

        if user_input.lower().startswith("/load "):
            load_knowledge_file(user_input[6:].strip())
            continue

        handle_user_input_sync(user_input)


# ═════════════════════════════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════════════════════════════

def main():
    print("\n╔══════════════════════════════════╗")
    print("║   Pocket is online. Hey user.   ║")
    print("╚══════════════════════════════════╝\n")

    bootstrap_knowledge()
    start_avatar_connection()

    # TTS worker thread
    tts_thread = threading.Thread(target=tts_worker, daemon=True)
    tts_thread.start()

    # F9 keyboard listener thread
    kb_thread = threading.Thread(target=keyboard_listener, daemon=True)
    kb_thread.start()

    # CLI runs on main thread
    cli_input_loop()


if __name__ == "__main__":
    main()
