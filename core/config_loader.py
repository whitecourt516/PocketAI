# core/config_loader.py
# Loads config/config.yaml and .env, exposes a single CFG dict.
# All other modules import from here — never from config.yaml directly.
#
# Usage:
#   from core.config_loader import CFG
#   model = CFG["llm"]["model"]
#   piper_exe = CFG["tts"]["piper_exe_abs"]   # absolute path, ready to use
#
# Stage 4s: ConfigLoader implements PocketModule.
#   health_check() verifies config loaded and all resolved paths exist.

import os
import yaml
from pathlib import Path
from dotenv import load_dotenv

from core.pocket_module import PocketModule

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
            return False
        except ValueError:
            pass
        if p == denied_abs:
            return False
    return True


def is_command_allowed(command: str) -> bool:
    """Return False if command contains any executor denylist entry."""
    lower = command.lower()
    return not any(blocked in lower for blocked in CFG["security"]["executor_denylist"])


# ═════════════════════════════════════════════════════════════════════════════
# LIFECYCLE — Stage 4s
# ═════════════════════════════════════════════════════════════════════════════

class ConfigLoader(PocketModule):
    """Lifecycle wrapper for config_loader.

    Config is loaded at import time (module-level above), so start() has
    nothing to do. health_check() verifies the CFG dict is populated and
    the three critical Piper paths actually exist on disk.
    """

    def start(self) -> None:
        # Config loads at import time — nothing to do here.
        pass

    def stop(self) -> None:
        # No connections or threads to close.
        pass

    def health_check(self) -> bool:
        try:
            if not CFG:
                return False
            # Verify the three resolved Piper paths exist
            for key in ("piper_exe_abs", "piper_model_abs", "piper_config_abs"):
                if not Path(CFG["tts"][key]).exists():
                    print(f"  [ConfigLoader] Missing path: {CFG['tts'][key]}")
                    return False
            return True
        except Exception as e:
            print(f"  [ConfigLoader] health_check error: {e}")
            return False

    def on_event(self, event: dict) -> None:
        # Config loader has no event subscriptions.
        pass


config_loader_module = ConfigLoader()
