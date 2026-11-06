# core/permissions.py
# Permission layer (4e) + Decision log (4e.1)
#
# Every real-world action Pocket wants to take passes through propose_action().
# Nothing executes without explicit approval. Every decision is logged.
#
# Public API:
#   propose_action(description, command) -> bool
#   log_decision(...)
#   record_outcome(command, outcome)
#
# Stage 4s: PermissionsModule implements PocketModule.
#   start()        — ensures the log directory exists
#   stop()         — no-op; JSONL log is append-only, nothing to flush
#   health_check() — verifies the log directory is writable
#   on_event()     — no subscriptions; permissions are synchronous by design

import json
import os
from datetime import datetime
from pathlib import Path

from core.config_loader import CFG, is_read_allowed, is_command_allowed
from core.pocket_module import PocketModule

# ── Log path ──────────────────────────────────────────────────────────────────
_core_dir    = Path(__file__).parent
PROJECT_ROOT = (_core_dir / "..").resolve()
LOG_DIR      = PROJECT_ROOT / "logs"
DECISION_LOG = LOG_DIR / "decisions.jsonl"


def _ensure_log_dir():
    LOG_DIR.mkdir(exist_ok=True)


# ═════════════════════════════════════════════════════════════════════════════
# DECISION LOG (unchanged public API)
# ═════════════════════════════════════════════════════════════════════════════

def log_decision(
    description: str,
    command: str,
    approved: bool,
    blocked_reason: str | None = None,
    outcome: str | None = None,
):
    _ensure_log_dir()
    record = {
        "timestamp":      datetime.now().isoformat(),
        "description":    description,
        "command":        command,
        "approved":       approved,
        "blocked_reason": blocked_reason,
        "outcome":        outcome,
    }
    with open(DECISION_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


# ═════════════════════════════════════════════════════════════════════════════
# PERMISSION GATE (unchanged public API)
# ═════════════════════════════════════════════════════════════════════════════

def propose_action(description: str, command: str) -> bool:
    blocked_reason = None

    if not is_command_allowed(command):
        blocked_reason = "command matches executor denylist"
        print(f"\n  [BLOCKED] {blocked_reason}")
        print(f"  Command: {command}\n")
        log_decision(description=description, command=command,
                     approved=False, blocked_reason=blocked_reason)
        return False

    if description.lower().startswith("read") or "/read" in description.lower():
        if not is_read_allowed(command):
            blocked_reason = "path matches read denylist"
            print(f"\n  [BLOCKED] {blocked_reason}")
            print(f"  Path: {command}\n")
            log_decision(description=description, command=command,
                         approved=False, blocked_reason=blocked_reason)
            return False

    print("\n" + "─" * 50)
    print("  Pocket wants to:")
    print(f"  {description}")
    print()
    print(f"  Command: {command}")
    print("─" * 50)

    try:
        response = input("  Approve? [y/n]: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        response = "n"

    approved = response == "y"

    log_decision(description=description, command=command, approved=approved)

    if approved:
        print("  [Approved]\n")
    else:
        print("  [Rejected]\n")

    return approved


def record_outcome(command: str, outcome: str):
    _ensure_log_dir()
    record = {
        "timestamp": datetime.now().isoformat(),
        "type":      "outcome",
        "command":   command,
        "outcome":   outcome,
    }
    with open(DECISION_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


# ═════════════════════════════════════════════════════════════════════════════
# LIFECYCLE — Stage 4s
# ═════════════════════════════════════════════════════════════════════════════

class PermissionsModule(PocketModule):
    """Lifecycle wrapper for the permission gate and decision log.

    start()        — creates the logs/ directory if it doesn't exist.
    stop()         — no-op; JSONL is append-only and closes after every write.
    health_check() — writes a canary file to logs/ to confirm write access,
                     then removes it. Returns False if the directory is
                     missing or the filesystem is read-only.
    on_event()     — no subscriptions; propose_action() is synchronous and
                     requires the user's direct input — it cannot be async.
    """

    def start(self) -> None:
        _ensure_log_dir()

    def stop(self) -> None:
        pass

    def health_check(self) -> bool:
        try:
            _ensure_log_dir()
            canary = LOG_DIR / ".health_check"
            canary.write_text("ok")
            canary.unlink()
            return True
        except Exception as e:
            print(f"  [PermissionsModule] health_check error: {e}")
            return False

    def on_event(self, event: dict) -> None:
        # Permissions are synchronous and require human input.
        # They cannot be triggered via the async event bus.
        pass


permissions_module = PermissionsModule()
