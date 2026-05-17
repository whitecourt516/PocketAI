# core/permissions.py
# Permission layer (4e) + Decision log (4e.1)
#
# Every real-world action Pocket wants to take passes through propose_action().
# Nothing executes without explicit approval. Every decision is logged.
#
# Public API:
#   propose_action(description, command) -> bool
#       Show user what Pocket wants to do, wait for y/n.
#       Returns True if approved, False if rejected or blocked.
#
#   log_decision(...)
#       Append one record to logs/decisions.jsonl.
#       Called automatically by propose_action — rarely needed directly.

import json
import os
from datetime import datetime
from pathlib import Path

from core.config_loader import CFG, is_read_allowed, is_command_allowed

# ── Log path ──────────────────────────────────────────────────────────────────
_core_dir    = Path(__file__).parent
PROJECT_ROOT = (_core_dir / "..").resolve()
LOG_DIR      = PROJECT_ROOT / "logs"
DECISION_LOG = LOG_DIR / "decisions.jsonl"


def _ensure_log_dir():
    LOG_DIR.mkdir(exist_ok=True)


# ═════════════════════════════════════════════════════════════════════════════
# DECISION LOG
# ═════════════════════════════════════════════════════════════════════════════

def log_decision(
    description: str,
    command: str,
    approved: bool,
    blocked_reason: str | None = None,
    outcome: str | None = None,
):
    """Append one decision record to logs/decisions.jsonl.

    Fields:
      timestamp      — ISO 8601
      description    — what Pocket said it wanted to do
      command        — the raw command/path/action string
      approved       — True if user said y, False if n or auto-blocked
      blocked_reason — set if auto-blocked by denylist before user saw it
      outcome        — filled in after execution (success, error message, etc.)
    """
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
# PERMISSION GATE
# ═════════════════════════════════════════════════════════════════════════════

def propose_action(description: str, command: str) -> bool:
    """Propose an action to user and wait for approval.

    Flow:
      1. Auto-block check — denylist (no prompt shown to user)
      2. Show proposal to user
      3. Wait for y/n
      4. Log the decision
      5. Return True (approved) or False (rejected/blocked)

    Args:
      description — plain English summary of what Pocket wants to do
      command     — the exact command, path, or action string

    Returns:
      True if user approved, False otherwise.
    """
    # ── Step 1: auto-block check ──────────────────────────────────────────────
    blocked_reason = None

    if not is_command_allowed(command):
        blocked_reason = "command matches executor denylist"
        print(f"\n  [BLOCKED] {blocked_reason}")
        print(f"  Command: {command}\n")
        log_decision(
            description=description,
            command=command,
            approved=False,
            blocked_reason=blocked_reason,
        )
        return False

    # /read path check — only applies when the action looks like a file read
    if description.lower().startswith("read") or "/read" in description.lower():
        if not is_read_allowed(command):
            blocked_reason = "path matches read denylist"
            print(f"\n  [BLOCKED] {blocked_reason}")
            print(f"  Path: {command}\n")
            log_decision(
                description=description,
                command=command,
                approved=False,
                blocked_reason=blocked_reason,
            )
            return False

    # ── Step 2: show proposal ─────────────────────────────────────────────────
    print("\n" + "─" * 50)
    print("  Pocket wants to:")
    print(f"  {description}")
    print()
    print(f"  Command: {command}")
    print("─" * 50)

    # ── Step 3: wait for approval ─────────────────────────────────────────────
    try:
        response = input("  Approve? [y/n]: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        response = "n"

    approved = response == "y"

    # ── Step 4: log it ────────────────────────────────────────────────────────
    log_decision(
        description=description,
        command=command,
        approved=approved,
    )

    # ── Step 5: confirm to user ──────────────────────────────────────────────
    if approved:
        print("  [Approved]\n")
    else:
        print("  [Rejected]\n")

    return approved


def record_outcome(command: str, outcome: str):
    """Update the most recent decision log entry for this command with its outcome.

    Call this after execution completes so the log has the full picture.
    Appends a follow-up outcome record rather than mutating the original
    (JSONL is append-only by design).
    """
    _ensure_log_dir()
    record = {
        "timestamp": datetime.now().isoformat(),
        "type":      "outcome",
        "command":   command,
        "outcome":   outcome,
    }
    with open(DECISION_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
