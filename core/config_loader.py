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
import shlex
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

# ── Inject computed project root ──────────────────────────────────────────────
# PROJECT_ROOT is derived from this file's location, so it's correct regardless
# of the launch CWD. This overrides any value in config.yaml on purpose — a
# committed config must not carry a machine-specific absolute path (A3).
CFG.setdefault("paths", {})["project_root"] = str(PROJECT_ROOT)

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


# Programs that, combined with an inline-exec flag, allow arbitrary code
# execution — always blocked regardless of the denylist.
_DANGEROUS_EXEC_COMBOS = [
    ("python",     "-c"),
    ("python3",    "-c"),
    ("powershell", "-c"),
    ("powershell", "-command"),
    ("pwsh",       "-c"),
    ("pwsh",       "-command"),
    ("cmd",        "/c"),
    ("bash",       "-c"),
    ("sh",         "-c"),
    ("node",       "-e"),
    ("ruby",       "-e"),
    ("perl",       "-e"),
]

# Shell metacharacters that indicate piping, redirection, or command chaining.
_SHELL_METACHARS = frozenset("|&;<>`")


def is_command_allowed(command: str) -> bool:
    """
    Return False if the command should be blocked.

    Checks (in order):
      1. Shell metacharacters — piping, redirection, chaining always blocked.
      2. Inline-exec combos  — python -c, powershell -c, etc. always blocked.
      3. Config denylist     — matched against parsed tokens, not raw substrings,
                               so spacing and case variations are caught correctly.

    Uses shlex parsing so 'rm  -rf' (extra spaces) and mixed case all match.
    Returns True (allowed) only if all checks pass.
    """
    # 1. Shell metacharacters
    if any(c in command for c in _SHELL_METACHARS):
        return False

    # 2. Parse the command — reject anything shlex can't tokenise
    try:
        parts = shlex.split(command)
    except ValueError:
        return False

    if not parts:
        return False

    program = Path(parts[0]).stem.lower()   # basename, no extension
    tokens  = [p.lower() for p in parts]

    # 3. Inline-exec combos
    for prog, flag in _DANGEROUS_EXEC_COMBOS:
        if program == prog and flag in tokens:
            return False

    # 4. Config denylist — parse each entry and match against tokens
    for blocked in CFG["security"]["executor_denylist"]:
        try:
            blocked_tokens = [p.lower() for p in shlex.split(blocked)]
        except ValueError:
            blocked_tokens = [blocked.lower().strip()]

        if not blocked_tokens:
            continue

        blocked_prog = Path(blocked_tokens[0]).stem.lower()

        # Single-token entry — match on program name
        if len(blocked_tokens) == 1 and blocked_prog == program:
            return False

        # Multi-token entry — all tokens must appear in the command
        if len(blocked_tokens) > 1 and all(bt in tokens for bt in blocked_tokens):
            return False

    return True


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
        pass

    def stop(self) -> None:
        pass

    def health_check(self) -> bool:
        try:
            if not CFG:
                return False
            for key in ("piper_exe_abs", "piper_model_abs", "piper_config_abs"):
                if not Path(CFG["tts"][key]).exists():
                    print(f"  [ConfigLoader] Missing path: {CFG['tts'][key]}")
                    return False
            return True
        except Exception as e:
            print(f"  [ConfigLoader] health_check error: {e}")
            return False

    def on_event(self, event: dict) -> None:
        pass


config_loader_module = ConfigLoader()