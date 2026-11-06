# core/executor.py
# Sandboxed shell command executor — every command passes through the
# permission gate before running.
#
# Security model (4.5c):
#   1. Secret-path check  — file-like args are checked against the read denylist
#                           before the approval prompt. /exec type .env is blocked
#                           here, not by the denylist in propose_action().
#   2. Command denylist   — is_command_allowed() blocks dangerous programs,
#                           shell metacharacters, and inline-exec combos via
#                           shlex parsing (not substring matching).
#   3. Approval gate      — every command that passes (1) and (2) still requires
#                           the user's explicit y/n before execution.
#   4. Constrained cwd    — subprocess runs from PROJECT_ROOT, not wherever the
#                           shell inherits. Limits blast radius of relative paths.
#
# Backup policy (documented, not enforced):
#   /exec writes are NOT routed through backup_manager. The executor runs
#   arbitrary shell commands — reliably intercepting writes inside them is not
#   feasible without a sandbox. Backup coverage for executor writes relies on
#   the Docker volume backup (Stage 4m). Do not represent /exec as backed-up.
#
# Stage 4s: ExecutorModule implements PocketModule.

import os
import shlex
import subprocess
from pathlib import Path

from core.permissions import propose_action, record_outcome
from core.config_loader import CFG, is_read_allowed, PROJECT_ROOT
from core.pocket_module import PocketModule
from core.logger import log


# ═════════════════════════════════════════════════════════════════════════════
# INTERNAL HELPERS
# ═════════════════════════════════════════════════════════════════════════════

def _check_command_paths(command: str) -> str | None:
    """
    Parse command arguments and check file-like tokens against the read denylist.

    Returns a human-readable reason string if any token resolves to a denied
    path, or None if the command is clear.

    This closes the /exec → .env leak: 'type .env' passes the command denylist
    (it's not a dangerous program) but is caught here before the approval prompt.
    """
    try:
        parts = shlex.split(command)
    except ValueError:
        return None  # unparseable — denylist check will handle it

    for token in parts[1:]:          # skip the program name
        if token.startswith("-") or token.startswith("/"):
            continue                 # skip flags

        candidate = Path(token)

        # Skip bare words that don't look like paths
        has_sep   = os.sep in token or "/" in token
        has_dot   = "." in token
        has_ext   = bool(candidate.suffix)
        if not (has_sep or has_dot or has_ext):
            continue

        resolved = (
            candidate.resolve()
            if candidate.is_absolute()
            else (PROJECT_ROOT / candidate).resolve()
        )

        if not is_read_allowed(str(resolved)):
            return f"references a denied path: {token}"

    return None


# ═════════════════════════════════════════════════════════════════════════════
# CORE FUNCTIONS (unchanged public API)
# ═════════════════════════════════════════════════════════════════════════════

def execute_command(command: str) -> str:
    # 1. Secret-path check — before any approval prompt
    path_block = _check_command_paths(command)
    if path_block:
        print(f"\n  [BLOCKED] executor {path_block}")
        print(f"  Command: {command}\n")
        log.command(command, approved=False)
        return f"[Execution blocked: {path_block}]"

    # 2. Denylist + approval gate
    description = "Execute shell command"
    approved    = propose_action(description, command)

    if not approved:
        log.command(command, approved=False)
        return "[Execution cancelled]"

    # 3. Run in constrained working directory
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=CFG["executor"]["timeout_seconds"],
            cwd=str(PROJECT_ROOT),
        )

        output = (
            result.stdout.strip()
            or result.stderr.strip()
            or "[Command completed with no output]"
        )

        record_outcome(command, output[:1000])
        log.command(command, approved=True, result=output)
        return output

    except subprocess.TimeoutExpired:
        outcome = "[Command timed out]"
        record_outcome(command, outcome)
        log.command(command, approved=True, result=outcome)
        return outcome

    except Exception as e:
        outcome = f"[Execution error: {e}]"
        record_outcome(command, outcome)
        log.command(command, approved=True, result=outcome)
        log.error("executor", outcome)
        return outcome


# ═════════════════════════════════════════════════════════════════════════════
# LIFECYCLE — Stage 4s
# ═════════════════════════════════════════════════════════════════════════════

class ExecutorModule(PocketModule):
    """Lifecycle wrapper for the sandboxed command executor.

    Stateless — calls subprocess on demand and delegates all approval and
    logging to permissions.py. start() and stop() are no-ops.
    health_check() confirms the denylist is populated so the executor never
    runs in an unconstrained state.
    on_event() handles 'executor.run' — still routes through propose_action().
    """

    def start(self) -> None:
        pass

    def stop(self) -> None:
        pass

    def health_check(self) -> bool:
        try:
            denylist = CFG.get("security", {}).get("executor_denylist", [])
            if not denylist:
                print("  [ExecutorModule] WARNING: executor denylist is empty")
                return False
            return True
        except Exception as e:
            print(f"  [ExecutorModule] health_check error: {e}")
            return False

    def on_event(self, event: dict) -> None:
        if event.get("type") != "executor.run":
            return
        command = event.get("command", "")
        if command:
            result = execute_command(command)
            print(f"  [Executor] {result}")


executor_module = ExecutorModule()