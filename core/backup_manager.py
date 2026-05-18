# core/backup_manager.py

import shutil
from datetime import datetime, timedelta
from pathlib import Path


# ── Paths ────────────────────────────────────────────────────────────────
_core_dir = Path(__file__).parent
PROJECT_ROOT = (_core_dir / "..").resolve()

BACKUP_DIR = Path(r"C:\Users\white\pocket_backups")


# ═════════════════════════════════════════════════════════════════════════
# Helpers
# ═════════════════════════════════════════════════════════════════════════

def _ensure_backup_dir():
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)


# ═════════════════════════════════════════════════════════════════════════
# Backup Creation
# ═════════════════════════════════════════════════════════════════════════

def backup_file(filepath: str) -> Path:
    """
    Create a timestamped backup of a file.

    Returns:
        Path to the created backup file.
    """

    _ensure_backup_dir()

    original = Path(filepath).resolve()

    if not original.exists():
        raise FileNotFoundError(f"File not found: {original}")

    if not original.is_file():
        raise ValueError(f"Not a file: {original}")

    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")

    backup_name = f"{timestamp}_{original.name}"
    backup_path = BACKUP_DIR / backup_name

    shutil.copy2(original, backup_path)

    return backup_path


# ═════════════════════════════════════════════════════════════════════════
# List Backups
# ═════════════════════════════════════════════════════════════════════════

def list_backups(filepath: str):
    """
    Return all backups matching a filename, newest first.
    """

    _ensure_backup_dir()

    target = Path(filepath).name

    backups = list(BACKUP_DIR.glob(f"*_{target}"))

    backups.sort(key=lambda p: p.stat().st_mtime, reverse=True)

    return backups


# ═════════════════════════════════════════════════════════════════════════
# Restore Latest Backup
# ═════════════════════════════════════════════════════════════════════════

def restore_latest_backup(filepath: str) -> str:
    """
    Restore the newest backup for a file.
    """

    original = Path(filepath).resolve()

    backups = list_backups(filepath)

    if not backups:
        return f"[No backups found for {original.name}]"

    latest = backups[0]

    # Backup current version before restoring
    if original.exists():
        backup_file(str(original))

    shutil.copy2(latest, original)

    return f"[Restored {original.name} from {latest.name}]"


# ═════════════════════════════════════════════════════════════════════════
# Prune Old Backups
# ═════════════════════════════════════════════════════════════════════════

def prune_old_backups(days: int = 30):
    """
    Delete backups older than X days.
    """

    _ensure_backup_dir()

    cutoff = datetime.now() - timedelta(days=days)

    for file in BACKUP_DIR.iterdir():

        if not file.is_file():
            continue

        modified = datetime.fromtimestamp(file.stat().st_mtime)

        if modified < cutoff:
            file.unlink()