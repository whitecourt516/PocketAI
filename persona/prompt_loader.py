import os

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
        return f.read()

SYSTEM_PROMPT = load_prompt("base_system.md")