# core/avatar_router.py
# Avatar routing — emotion detection, content classification, and reply dispatch.
#
# Public API:
#   send_to_avatar(response_text) — detect emotion + content type, route to avatar
#
# Stage 4s: AvatarRouterModule implements PocketModule.
#   start()        — no-op; expressions.json is loaded at import time
#   stop()         — no-op; pure functions, no threads or connections
#   health_check() — verifies EMOTION_RULES loaded and is non-empty
#   on_event()     — handles "avatar_router.send" events from the bus (4q)

import json
import os
import re

from core.websocket_server import websocket_module
from core.pocket_module import PocketModule
from core.state_manager import state

# ── Load expression rules ─────────────────────────────────────────────────────
_core_dir         = os.path.dirname(os.path.abspath(__file__))
_project_root     = os.path.join(_core_dir, '..')
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
    state.set_thinking(True)

    emotion      = detect_emotion(response_text)
    content_type = detect_content_type(response_text)

    websocket_module.send({"type": "expression", "value": emotion})
    state.set_expression(emotion, "avatar_router")

    if content_type == "subtitle":
        duration = max(3000, len(response_text) * 60)
        websocket_module.send({"type": "speech", "text": response_text, "duration": duration})
        websocket_module.send({"type": "panel_close"})
    elif content_type == "code":
        code = extract_code(response_text)
        websocket_module.send({"type": "speech", "text": "Here's the code ↘", "duration": 3000})
        websocket_module.send({"type": "panel", "content": code, "contentType": "code", "title": "Code"})
    else:
        first = response_text.split('.')[0].strip() + '.'
        websocket_module.send({"type": "speech", "text": truncate_subtitle(first), "duration": 4000})
        websocket_module.send({"type": "panel", "content": response_text, "contentType": content_type, "title": "Pocket"})

    websocket_module.send({"type": "wander_resume"})
    state.set_thinking(False)


# ═════════════════════════════════════════════════════════════════════════════
# LIFECYCLE — Stage 4s
# ═════════════════════════════════════════════════════════════════════════════

class AvatarRouterModule(PocketModule):
    """Lifecycle wrapper for avatar_router.

    This module is pure functions — no threads, no connections, no state
    beyond the expressions.json data loaded at import time.
    start() and stop() are no-ops. health_check() confirms the rules loaded.
    on_event() handles "avatar_router.send" for bus-driven routing (4q).
    """

    def start(self) -> None:
        # expressions.json is loaded at import time — nothing to do.
        pass

    def stop(self) -> None:
        # Pure functions — nothing to tear down.
        pass

    def health_check(self) -> bool:
        try:
            return len(EMOTION_RULES) > 0
        except Exception as e:
            print(f"  [AvatarRouterModule] health_check error: {e}")
            return False

    def on_event(self, event: dict) -> None:
        # Supported event: {"type": "avatar_router.send", "text": "..."}
        if event.get("type") != "avatar_router.send":
            return
        text = event.get("text", "")
        if text:
            send_to_avatar(text)


avatar_router_module = AvatarRouterModule()
