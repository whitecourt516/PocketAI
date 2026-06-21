"""
core/health_check.py — Stage 4j Startup Health Checks

Runs health_check() on each registered module via the PocketModule interface (4s).
Critical failures halt startup. Non-critical failures warn and prompt user to confirm.
After all checks pass, emits a health_summary event to the avatar (for 4t overlay).
"""

import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.websocket_server import send_dict_to_avatar

# ─── Service registry ────────────────────────────────────────────────────────
#
# Each entry:
#   name       — display label
#   module_key — key to pull the live module instance from the registry dict
#   critical   — if True, failure halts startup; if False, user is prompted
#
SERVICE_REGISTRY = [
    {"name": "Ollama LLM",   "module_key": "llm",    "critical": True},
    {"name": "ChromaDB",     "module_key": "memory", "critical": True},
    {"name": "Piper TTS",    "module_key": "tts",    "critical": False},
    {"name": "Avatar / WS",  "module_key": "ws",     "critical": False},
]

# ─── ANSI colours (Windows-safe via colorama if available, fallback to plain) ─
try:
    from colorama import init as colorama_init, Fore, Style
    colorama_init()
    GREEN  = Fore.GREEN  + Style.BRIGHT
    YELLOW = Fore.YELLOW + Style.BRIGHT
    RED    = Fore.RED    + Style.BRIGHT
    RESET  = Style.RESET_ALL
except ImportError:
    GREEN = YELLOW = RED = RESET = ""

_CHECK  = f"{GREEN}✅{RESET}"
_WARN   = f"{YELLOW}⚠️ {RESET}"
_FAIL   = f"{RED}❌{RESET}"
_SKIP   = "⏭ "


def _status_line(index: int, total: int, name: str, symbol: str, note: str = "") -> str:
    note_str = f" — {note}" if note else ""
    return f"  [{index}/{total}] {symbol} {name}{note_str}"


def run_startup_checks(modules: dict, send_to_avatar_fn=None) -> bool:
    """
    Run health checks for all registered services.

    Args:
        modules:            dict mapping module_key → PocketModule instance (or None)
        send_to_avatar_fn:  callable(command_dict) to send events to Electron avatar

    Returns:
        True if startup should proceed, False if it should abort.
    """
    total   = len(SERVICE_REGISTRY)
    results = {}  # module_key → "ok" | "warn" | "fail" | "missing"

    print()
    print("─" * 48)
    print("  Pocket — Startup Health Check")
    print("─" * 48)

    non_critical_failures = []

    for i, service in enumerate(SERVICE_REGISTRY, start=1):
        name       = service["name"]
        key        = service["module_key"]
        critical   = service["critical"]
        module     = modules.get(key)

        if module is None:
            # Module not registered — treat same as non-critical warn or critical fail
            symbol = _FAIL if critical else _WARN
            note   = "not registered"
            print(_status_line(i, total, name, symbol, note))
            results[key] = "missing"
            if critical:
                print()
                print(f"  {RED}CRITICAL: {name} is not registered. Cannot start.{RESET}")
                print("─" * 48)
                return False
            else:
                non_critical_failures.append(name)
            continue

        try:
            ok = module.health_check()
        except Exception as exc:
            ok = False
            _exc_note = str(exc)[:80]

        if ok:
            print(_status_line(i, total, name, _CHECK))
            results[key] = "ok"
        else:
            if critical:
                print(_status_line(i, total, name, _FAIL, "CRITICAL"))
                print()
                print(f"  {RED}CRITICAL: {name} failed health check. Cannot start.{RESET}")
                print("─" * 48)
                return False
            else:
                print(_status_line(i, total, name, _WARN, "degraded"))
                results[key] = "warn"
                non_critical_failures.append(name)

    # ── All critical services passed ──────────────────────────────────────────

    if non_critical_failures:
        print()
        print(f"  {YELLOW}Non-critical service(s) unavailable:{RESET}")
        for svc in non_critical_failures:
            print(f"    • {svc}")
        print()
        print("  Pocket can run in degraded mode, but some features will be limited.")
        print()

        try:
            answer = input("  Continue anyway? [y/N] ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            answer = "n"

        if answer != "y":
            print()
            print("  Startup cancelled.")
            print("─" * 48)
            return False

    print()
    print(f"  {GREEN}Pocket is online.{RESET}")
    print("─" * 48)
    print()

    # ── Emit health summary to avatar for 4t overlay ──────────────────────────
    if send_to_avatar_fn is not None:
        health_summary = {
            "type": "health_summary",
            "services": {
                key: results.get(key, "ok")
                for service in SERVICE_REGISTRY
                for key in [service["module_key"]]
            },
            "degraded": non_critical_failures,
        }
        try:
            send_to_avatar_fn(health_summary)
        except Exception:
            pass  # Avatar event failure must never block startup

    return True
