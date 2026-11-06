import os
import re

from core.config_loader import CFG

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

def load_prompt(filename):
    path = os.path.join(
        PROJECT_ROOT,
        "persona",
        "prompts",
        filename
    )

    with open(path, "r", encoding="utf-8") as f:
        return _fill_user_name(f.read())

def _fill_user_name(text: str) -> str:
    # Prompts say {user_name}; the real name comes from POCKET_USER_NAME in .env
    name = CFG.get("user_name") or "the user"
    # Capitalise at the start of a line, sentence or bold span
    text = re.sub(r"(^|[.!?]\s+|\*\*|- )\{user_name\}", lambda m: m.group(1) + name[0].upper() + name[1:], text, flags=re.M)
    return text.replace("{user_name}", name)

def build_system_prompt() -> str:
    parts = [
        load_prompt("base_system.md"),
        load_prompt("core_identity.md"),
        load_prompt("authority.md"),
        load_prompt("memory_principles.md"),
    ]
    return "\n\n".join(parts)