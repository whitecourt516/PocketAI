# core/executor.py
# Sandboxed shell command executor — every command passes through the
# permission gate before running.
#
# Stage 4s: ExecutorModule implements PocketModule.
#   start()        — no-op; subprocess is called on demand
#   stop()         — no-op; no persistent processes or threads
#   health_check() — verifies the executor denylist is populated in CFG
#   on_event()     — handles "executor.run" events from the bus (4q)
#                    Note: bus-driven execution still goes through propose_action()

import subprocess

from core.permissions import propose_action, record_outcome
from core.config_loader import CFG
from core.pocket_module import PocketModule


# ═════════════════════════════════════════════════════════════════════════════
# CORE FUNCTIONS (unchanged public API)
# ═════════════════════════════════════════════════════════════════════════════

def execute_command(command: str) -> str:
    description = "Execute shell command"

    approved = propose_action(description, command)

    if not approved:
        return "[Execution cancelled]"

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=CFG["executor"]["timeout_seconds"]
        )

        output = (
            result.stdout.strip()
            or result.stderr.strip()
            or "[Command completed with no output]"
        )

        record_outcome(command, output[:1000])
        return output

    except subprocess.TimeoutExpired:
        outcome = "[Command timed out]"
        record_outcome(command, outcome)
        return outcome

    except Exception as e:
        outcome = f"[Execution error: {e}]"
        record_outcome(command, outcome)
        return outcome


# ═════════════════════════════════════════════════════════════════════════════
# LIFECYCLE — Stage 4s
# ═════════════════════════════════════════════════════════════════════════════

class ExecutorModule(PocketModule):
    """Lifecycle wrapper for the sandboxed command executor.

    This module is stateless — it calls subprocess on demand and delegates
    all approval and logging to permissions.py. start() and stop() are
    no-ops. health_check() confirms the denylist is in place so the executor
    can never run in an unconstrained state.
    on_event() handles "executor.run" — still routes through propose_action().
    """

    def start(self) -> None:
        # Stateless — nothing to initialise.
        pass

    def stop(self) -> None:
        # No persistent processes or threads.
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
        # Supported event: {"type": "executor.run", "command": "..."}
        # Bus-triggered execution still requires user's approval via propose_action().
        if event.get("type") != "executor.run":
            return
        command = event.get("command", "")
        if command:
            result = execute_command(command)
            print(f"  [Executor] {result}")


executor_module = ExecutorModule()
