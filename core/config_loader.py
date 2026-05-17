# core/config_loader.py
# Loads config/config.yaml and .env, exposes a single CFG dict.
# All other modules import from here — never from config.yaml directly.
#
# Usage:
#   from core.config_loader import CFG
#   model = CFG["llm"]["model"]
#   piper_exe = CFG["tts"]["piper_exe_abs"]   # absolute path, ready to use

import os
import yaml
from pathlib import Path
from dotenv import load_dotenv

# ── Paths ─────────────────────────────────────────────────────────────────────
_core_dir     = Path(__file__).parent
PROJECT_ROOT  = (_core_dir / "..").resolve()
_config_path  = PROJECT_ROOT / "config" / "config.yaml"
_env_path     = PROJECT_ROOT / ".env"

# ── Load .env first (so env vars are available before yaml is read) ───────────
load_dotenv(_env_path)

# ── Load config.yaml ──────────────────────────────────────────────────────────
with open(_config_path, "r", encoding="utf-8") as f:
    CFG: dict = yaml.safe_load(f)

# ── Apply .env overrides ──────────────────────────────────────────────────────
if os.getenv("OLLAMA_HOST"):
    CFG["llm"]["host"] = os.getenv("OLLAMA_HOST")

if os.getenv("PIPER_EXE"):
    CFG["tts"]["piper_exe"] = os.getenv("PIPER_EXE")

if os.getenv("PIPER_MODEL"):
    CFG["tts"]["piper_model"] = os.getenv("PIPER_MODEL")

# ── Resolve relative paths to absolute ───────────────────────────────────────
# Piper paths in config.yaml are relative to project root.
# These _abs variants are ready to pass directly to subprocess / os.path.exists.
def _abs(relative: str) -> str:
    p = Path(relative)
    return str(p if p.is_absolute() else PROJECT_ROOT / p)

CFG["tts"]["piper_exe_abs"]    = _abs(CFG["tts"]["piper_exe"])
CFG["tts"]["piper_model_abs"]  = _abs(CFG["tts"]["piper_model"])
CFG["tts"]["piper_config_abs"] = _abs(CFG["tts"]["piper_config"])
CFG["memory"]["chroma_path"]   = str(PROJECT_ROOT / "chroma_data")

# ── Security helpers ──────────────────────────────────────────────────────────

def is_read_allowed(filepath: str) -> bool:
    """Return False if filepath matches anything in the read denylist."""
    p = Path(filepath).resolve()
    for denied in CFG["security"]["read_denylist"]:
        denied_abs = (PROJECT_ROOT / denied).resolve()
        try:
            p.relative_to(denied_abs)
            return False  # filepath is inside a denied path
        except ValueError:
            pass
        if p == denied_abs:
            return False
    return True


def is_command_allowed(command: str) -> bool:
    """Return False if command contains any executor denylist entry."""
    lower = command.lower()
    return not any(blocked in lower for blocked in CFG["security"]["executor_denylist"])
