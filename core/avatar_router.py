# core/avatar_router.py
# Avatar routing — emotion detection, content classification, and reply dispatch.
#
# Public API:
#   send_to_avatar(response_text) — detect emotion + content type, route to avatar

import json
import os
import re

from core.websocket_server import (
    avatar_expression,
    avatar_subtitle,
    avatar_panel,
    avatar_panel_close,
    avatar_done_thinking,
)

# ── Load expression rules ─────────────────────────────────────────────────────
_core_dir        = os.path.dirname(os.path.abspath(__file__))
_project_root    = os.path.join(_core_dir, '..')
_expressions_path = os.path.join(_project_root, "config", "expressions.json")

with open(_expressions_path, "r", encoding="utf-8") as f:
    _expressions = json.load(f)

EMOTION_RULES = list(_expressions.items())

MAX_SUBTITLE_LEN = 120


# ═════════════════════════════════════════════════════════════════════════════
# DETECTION
# ═════════════════════════════════════════════════════════════════════════════

def detect_emotion(text: str) -> str:
    """Return the first matching emotion from EMOTION_RULES, or 'neutral'."""
    lower = text.lower()
    for emotion, keywords in EMOTION_RULES:
        if any(kw in lower for kw in keywords):
            return emotion
    return "neutral"


def detect_content_type(text: str) -> str:
    """Classify response text as subtitle, code, markdown, or text."""
    if "```" in text:
        return "code"
    if len(text) > MAX_SUBTITLE_LEN and (
        "#" in text or "\n-" in text or "\n*" in text
    ):
        return "markdown"
    if len(text) > MAX_SUBTITLE_LEN:
        return "text"
    return "subtitle"


def extract_code(text: str) -> str:
    """Pull code blocks out of a markdown-fenced response."""
    matches = re.findall(r"```(?:\w+)?\n?(.*?)```", text, re.DOTALL)
    return "\n\n".join(m.strip() for m in matches) if matches else text


def truncate_subtitle(text: str) -> str:
    """Truncate text to MAX_SUBTITLE_LEN, breaking on a word boundary."""
    text = text.strip()
    if len(text) <= MAX_SUBTITLE_LEN:
        return text
    return text[:MAX_SUBTITLE_LEN].rsplit(' ', 1)[0] + "…"


# ═════════════════════════════════════════════════════════════════════════════
# ROUTER
# ═════════════════════════════════════════════════════════════════════════════

def send_to_avatar(response_text: str):
    """Route Pocket's reply to the avatar — expression + subtitle or panel."""
    emotion      = detect_emotion(response_text)
    content_type = detect_content_type(response_text)

    avatar_expression(emotion)

    if content_type == "subtitle":
        duration = max(3000, len(response_text) * 60)
        avatar_subtitle(response_text, duration)
        avatar_panel_close()
    elif content_type == "code":
        code = extract_code(response_text)
        avatar_subtitle("Here's the code ↘", 3000)
        avatar_panel(code, "code", "Code")
    else:
        first = response_text.split('.')[0].strip() + '.'
        avatar_subtitle(truncate_subtitle(first), 4000)
        avatar_panel(response_text, content_type, "Pocket")

    avatar_done_thinking()
