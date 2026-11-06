# core/file_editor.py
# Sanctioned file-modification path for Pocket self-edits.
#
# Enforces, in order:  path guard → existence guard → content validation →
# approval → automatic backup → write → log. This is the ONLY route Pocket
# should use to modify its own config/persona files. Raw /exec shell writes
# skip the backup; this does not. That's what makes the 4g.1 guarantee — "a
# backup before any approved file modification, no exceptions" — actually hold.
#
# By default safe_write only MODIFIES existing files; a non-existent path is
# refused (likely a typo) unless allow_create=True is passed explicitly.
# .json/.yaml content must parse before anything is written, so a bad self-edit
# can't brick startup.
#
# Critical safety property: if the target exists and the backup FAILS, the
# write is aborted. No backup → no write.
#
# Public API:
#   safe_write(filepath, content) -> str
#
# Stage 4s: FileEditorModule implements PocketModule.
#   start()        — no-op; stateless
#   stop()         — no-op
#   health_check() — confirms the project root resolves (write target base)
#   on_event()     — handles "file.write" events; still routes through approval

import json
from pathlib import Path

from core.permissions import propose_action, record_outcome
from core.config_loader import is_read_allowed, PROJECT_ROOT
from core.backup_manager import backup_file
from core.pocket_module import PocketModule
from core.logger import log


# ═════════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ═════════════════════════════════════════════════════════════════════════════

def safe_write(filepath: str, content: str, allow_create: bool = False) -> str:
    """Approve → back up → write. The sanctioned path for Pocket self-edits.

    By default this only MODIFIES existing files — a path that doesn't exist is
    refused, because for self-edits a missing path almost always means a typo
    (and silently creating a new file means writing with no backup). Pass
    allow_create=True only when you genuinely intend a new file.

    Returns a human-readable status string (never raises on expected failures).
    """
    path = Path(filepath)
    path = path.resolve() if path.is_absolute() else (PROJECT_ROOT / filepath).resolve()

    # Reuse the read denylist as a write guard — never clobber .env, chroma_data,
    # backups, etc. (A dedicated write_denylist can be added later if read/write
    # ever need to diverge.) This check runs BEFORE any approval prompt.
    if not is_read_allowed(str(path)):
        log.command(f"write {path}", approved=False)
        return f"[Write blocked: {path.name} is on the denylist]"

    existed = path.exists()

    # Refuse to create a brand-new file from a likely-mistyped path. This is the
    # guard that stops a fat-fingered path (e.g. "expressions.json {") from
    # silently writing junk with no backup.
    if not existed and not allow_create:
        return (f"[Write refused: {path.name} does not exist — did you mistype the path? "
                f"Pass allow_create=True to intentionally create a new file.]")

    # Validate structured content BEFORE touching disk. A self-edit that writes
    # un-parseable JSON/YAML to a file the app loads at boot will brick startup,
    # so refuse it here rather than relying on the backup to clean up after.
    suffix = path.suffix.lower()
    if suffix == ".json":
        try:
            json.loads(content)
        except json.JSONDecodeError as e:
            return f"[Write refused: content is not valid JSON — {e}]"
    elif suffix in (".yaml", ".yml"):
        try:
            import yaml
            yaml.safe_load(content)
        except Exception as e:
            return f"[Write refused: content is not valid YAML — {e}]"

    command = f"write {path} ({len(content)} chars, {'overwrite' if existed else 'new file'})"

    if not propose_action(f"Modify file: {path.name}", command):
        log.command(command, approved=False)
        return "[Write cancelled]"

    # Automatic backup BEFORE modifying — 4g.1, no exceptions.
    # If the file exists and the backup fails, abort: no backup → no write.
    backup_note = ""
    if existed:
        try:
            backup_path = backup_file(str(path))
            backup_note = f" (backup: {backup_path.name})"
        except Exception as e:
            outcome = f"[Backup failed — write aborted: {e}]"
            record_outcome(command, outcome)
            log.error("file_editor", outcome)
            return outcome

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    except Exception as e:
        outcome = f"[Write error: {e}]"
        record_outcome(command, outcome)
        log.error("file_editor", outcome)
        return outcome

    outcome = f"[Wrote {path.name}{backup_note}]"
    record_outcome(command, outcome)
    log.command(command, approved=True, result=outcome)
    return outcome


# ═════════════════════════════════════════════════════════════════════════════
# LIFECYCLE — Stage 4s
# ═════════════════════════════════════════════════════════════════════════════

class FileEditorModule(PocketModule):
    """Lifecycle wrapper for the sanctioned file-write path.

    Stateless — all approval, backup, and logging are delegated. start()/stop()
    are no-ops. health_check() confirms the project root resolves so writes have
    a valid base. on_event() handles "file.write" for future bus-driven edits
    (Stage 8a/8f) — still gated by propose_action() inside safe_write().
    """

    def start(self) -> None:
        pass

    def stop(self) -> None:
        pass

    def health_check(self) -> bool:
        try:
            return PROJECT_ROOT.exists() and PROJECT_ROOT.is_dir()
        except Exception as e:
            print(f"  [FileEditorModule] health_check error: {e}")
            return False

    def on_event(self, event: dict) -> None:
        # Supported event: {"type": "file.write", "filepath": "...", "content": "..."}
        # Bus-triggered writes still require the user's approval via safe_write().
        if event.get("type") != "file.write":
            return
        filepath = event.get("filepath", "")
        content  = event.get("content")
        if filepath and content is not None:
            result = safe_write(filepath, content)
            print(f"  [FileEditor] {result}")


file_editor_module = FileEditorModule()
