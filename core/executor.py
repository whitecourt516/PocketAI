# core/executor.py

import subprocess

from core.permissions import propose_action, record_outcome
from core.config_loader import CFG


def execute_command(command: str) -> str:
    description = f"Execute shell command"

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