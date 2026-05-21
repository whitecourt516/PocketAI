# core/backup_manager.py
# File backup, restore, and pruning utilities.
#
# Stage 4s: BackupManagerModule implements PocketModule.
#   start()        — ensures the backup directory exists
#   stop()         — no-op; no threads or connections
#   health_check() — verifies backup directory exists and is writable
#   on_event()     — handles "backup.file" events from the bus (4q)

import shutil
from datetime import datetime, timedelta
from pathlib import Path

from core.pocket_module import PocketModule

# ── Paths ────────────────────────────────────────────────────────────────
_core_dir = Path(__file__).parent
PROJECT_ROOT = (_core_dir / "..").resolve()

BACKUP_DIR = Path(r"C:\Users\white\pocket_backups")


# ═════════════════════════════════════════════════════════════════════════
# HELPERS
# ═════════════════════════════════════════════════════════════════════════

def _ensure_backup_dir():
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)


# ═════════════════════════════════════════════════════════════════════════
# CORE FUNCTIONS (unchanged public API)
# ═════════════════════════════════════════════════════════════════════════

def backup_file(filepath: str) -> Path:
    """Create a timestamped backup of a file. Returns path to backup."""
    _ensure_backup_dir()
    original = Path(filepath).resolve()

    if not original.exists():
        raise FileNotFoundError(f"File not found: {original}")
    if not original.is_file():
        raise ValueError(f"Not a file: {original}")

    timestamp   = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    backup_name = f"{timestamp}_{original.name}"
    backup_path = BACKUP_DIR / backup_name

    shutil.copy2(original, backup_path)
    return backup_path


def list_backups(filepath: str):
    """Return all backups matching a filename, newest first."""
    _ensure_backup_dir()
    target  = Path(filepath).name
    backups = list(BACKUP_DIR.glob(f"*_{target}"))
    backups.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return backups


def restore_latest_backup(filepath: str) -> str:
    """Restore the newest backup for a file."""
    original = Path(filepath).resolve()
    backups  = list_backups(filepath)

    if not backups:
        return f"[No backups found for {original.name}]"

    latest = backups[0]

    if original.exists():
        backup_file(str(original))

    shutil.copy2(latest, original)
    return f"[Restored {original.name} from {latest.name}]"


def prune_old_backups(days: int = 30):
    """Delete backups older than X days."""
    _ensure_backup_dir()
    cutoff = datetime.now() - timedelta(days=days)

    for file in BACKUP_DIR.iterdir():
        if not file.is_file():
            continue
        modified = datetime.fromtimestamp(file.stat().st_mtime)
        if modified < cutoff:
            file.unlink()


# ═════════════════════════════════════════════════════════════════════════
# LIFECYCLE — Stage 4s
# ═════════════════════════════════════════════════════════════════════════

class BackupManagerModule(PocketModule):
    """Lifecycle wrapper for backup_manager.

    start()        — ensures the backup directory exists before anything tries
                     to write to it. Called before any file-modifying module starts.
    stop()         — no-op; backups are individual files, no flush needed.
    health_check() — writes a canary file to BACKUP_DIR to confirm write access,
                     then removes it.
    on_event()     — handles "backup.file" so other modules can trigger a backup
                     without importing backup_manager directly.
    """

    def start(self) -> None:
        _ensure_backup_dir()

    def stop(self) -> None:
        pass

    def health_check(self) -> bool:
        try:
            _ensure_backup_dir()
            canary = BACKUP_DIR / ".health_check"
            canary.write_text("ok")
            canary.unlink()
            return True
        except Exception as e:
            print(f"  [BackupManagerModule] health_check error: {e}")
            return False

    def on_event(self, event: dict) -> None:
        # Supported event: {"type": "backup.file", "filepath": "..."}
        if event.get("type") != "backup.file":
            return
        filepath = event.get("filepath", "")
        if filepath:
            try:
                path = backup_file(filepath)
                print(f"  [BackupManager] Backed up to {path}")
            except Exception as e:
                print(f"  [BackupManager] Backup failed: {e}")


backup_manager_module = BackupManagerModule()
