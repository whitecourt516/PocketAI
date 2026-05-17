# config/settings.py
# Backwards-compatibility shim.
# All values now live in config/config.yaml and are loaded via core/config_loader.
# Modules should migrate to: from core.config_loader import CFG
# This shim keeps existing imports working during the transition.

from core.config_loader import CFG

MODEL        = CFG["llm"]["model"]

COLLECTION_NAME = CFG["memory"]["collection_name"]
N_MEMORIES      = CFG["memory"]["n_results"]
KNOWLEDGE_FILES = CFG["memory"]["knowledge_files"]

WHISPER_MODEL     = CFG["stt"]["whisper_model"]
SAMPLE_RATE       = CFG["stt"]["sample_rate"]
CHANNELS          = CFG["stt"]["channels"]
SILENCE_THRESHOLD = CFG["stt"]["silence_threshold"]
SILENCE_DURATION  = CFG["stt"]["silence_duration"]
MAX_RECORD_SECS   = CFG["stt"]["max_record_secs"]

TYPING_CHARS_PER_SEC = CFG["tts"]["typing_chars_per_sec"]

WEBSOCKET_PORT = CFG["avatar"]["websocket_port"]
