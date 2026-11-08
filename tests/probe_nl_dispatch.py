# tests/probe_nl_dispatch.py
# Manual probe for 4.5f NL dispatch — asks the LIVE model a few prompts with the
# registry's tools offered and prints what comes back. Executes nothing: it only
# shows whether the model emits structured tool_calls.
# Run: python -m tests.probe_nl_dispatch   (from project root, venv active, Ollama up)
#
# Two modes per prompt:
#   bare  — just the user message + TOOL_GUIDANCE
#   full  — Pocket's real system prompt (build_system_prompt) + TOOL_GUIDANCE
# If "bare" calls tools and "full" doesn't, the persona prompt is drowning the
# tool instruction. If neither does, the model itself isn't calling tools.
# Reusable for the Qwen eval: change MODEL in config.yaml and rerun.

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pocket  # noqa: F401 — registers the tools (main() does not run on import)
from config.settings import MODEL
from core.nl_dispatch import TOOL_GUIDANCE
from core.ollama_client import chat_message
from core.tool_registry import registry
from persona.prompt_loader import build_system_prompt

PROMPTS = [
    "How many memories do you have stored?",
    "Read README.md and tell me what it says.",
    "Hey, how's it going?",  # should NOT call a tool
]


def main():
    tools = registry.to_ollama_tools()
    print(f"Model: {MODEL}")
    print(f"Tools offered: {[t['function']['name'] for t in tools]}\n")

    systems = {
        "bare": TOOL_GUIDANCE,
        "full": build_system_prompt() + "\n\n" + TOOL_GUIDANCE,
    }
    for prompt in PROMPTS:
        print("=" * 70)
        print(f"PROMPT: {prompt}")
        for mode, system in systems.items():
            msg = chat_message(
                [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
                tools=tools,
            )
            print(f"  [{mode}] tool_calls: {msg['tool_calls'] or 'none'}")
            text = (msg["content"] or "").strip().replace("\n", " ")
            print(f"  [{mode}] content:    {text[:160] or '(empty)'}")
        print()


if __name__ == "__main__":
    main()
