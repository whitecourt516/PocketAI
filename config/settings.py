# config/settings.py

# LLM
MODEL = "llama3.1"

# Memory
COLLECTION_NAME = "personal_memory"
N_MEMORIES      = 6

# Knowledge files to seed on first run (relative to project root)
KNOWLEDGE_FILES = [
    "pocket_project_notes.md",
    "pocket_master_roadmap.md",
    "about-me.md",
]

# Audio / STT
WHISPER_MODEL     = "base"
SAMPLE_RATE       = 16000
CHANNELS          = 1
SILENCE_THRESHOLD = 0.01
SILENCE_DURATION  = 1.5
MAX_RECORD_SECS   = 30

# TTS
TYPING_CHARS_PER_SEC = 40

# WebSocket
WEBSOCKET_PORT = 8765