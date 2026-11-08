# core/logger.py
# Stage 4i — Structured Logging
# Writes structured JSONL entries to logs/pocket.jsonl.
# Rotates daily, keeps 7 days. One entry per line, easy to parse.
#
# Usage:
#   from core.logger import log
#   log.command("echo hello", approved=True, result="hello")
#   log.expression("happy", source="avatar_router")
#   log.memory_retrieval(query="what is pocket", results=3)
#   log.websocket("CONNECTED", attempt=0)
#   log.error("module_name", "something went wrong")
#
# Stage 4s: LoggerModule implements PocketModule.

import json
import os
import threading
from datetime import datetime, timedelta
from logging.handlers import TimedRotatingFileHandler
from core.pocket_module import PocketModule
from core.config_loader import CFG


# ═════════════════════════════════════════════════════════════════════════════
# STRUCTURED LOGGER
# ═════════════════════════════════════════════════════════════════════════════

class StructuredLogger:
    """
    Writes JSONL entries to logs/pocket.jsonl.
    Thread-safe. Rotates daily, retains 7 days.
    Each entry is a JSON object on its own line with a timestamp and type field.
    """

    def __init__(self):
        self._lock       = threading.Lock()
        self._handler    = None
        self._log_path   = None
        self._ready      = False

    def init(self, log_dir: str = None, retention_days: int = 7) -> None:
        """
        Call once on startup (via LoggerModule.start()).
        log_dir defaults to logs/ in the project root.
        """
        if log_dir is None:
            project_root = CFG.get("paths", {}).get("project_root", ".")
            log_dir = os.path.join(project_root, "logs")

        os.makedirs(log_dir, exist_ok=True)
        self._log_path = os.path.join(log_dir, "pocket.jsonl")

        self._handler = TimedRotatingFileHandler(
            filename    = self._log_path,
            when        = "midnight",
            interval    = 1,
            backupCount = retention_days,
            encoding    = "utf-8",
            utc         = False,
        )
        self._ready = True

    # ------------------------------------------------------------------
    # Core write
    # ------------------------------------------------------------------

    def _write(self, entry: dict) -> None:
        if not self._ready:
            return
        entry["ts"] = datetime.now().isoformat(timespec="seconds")
        line = json.dumps(entry, ensure_ascii=False)
        with self._lock:
            try:
                if self._handler.shouldRollover(None):
                    self._handler.doRollover()
                if self._handler.stream is None:
                    self._handler.stream = self._handler._open()
                self._handler.stream.write(line + "\n")
                self._handler.stream.flush()
            except Exception as e:
                print(f"  [Logger] write failed: {e}")

    # ------------------------------------------------------------------
    # Typed log methods
    # ------------------------------------------------------------------

    def command(self, command: str, approved: bool, result: str = None) -> None:
        self._write({
            "type":     "command",
            "command":  command,
            "approved": approved,
            "result":   result[:500] if result else None,
        })

    def expression(self, expression: str, source: str) -> None:
        self._write({
            "type":       "expression",
            "expression": expression,
            "source":     source,
        })

    def memory_retrieval(self, query: str, results: int, collection: str = "personal_memory") -> None:
        self._write({
            "type":       "memory_retrieval",
            "query":      query[:200],
            "results":    results,
            "collection": collection,
        })

    def websocket(self, status: str, attempt: int = 0, reason: str = None) -> None:
        self._write({
            "type":    "websocket",
            "status":  status,
            "attempt": attempt,
            "reason":  reason,
        })

    def error(self, module: str, message: str) -> None:
        self._write({
            "type":    "error",
            "module":  module,
            "message": message[:500],
        })

    def info(self, module: str, message: str) -> None:
        self._write({
            "type":    "info",
            "module":  module,
            "message": message[:500],
        })


# ═════════════════════════════════════════════════════════════════════════════
# LIFECYCLE — Stage 4s
# ═════════════════════════════════════════════════════════════════════════════

class LoggerModule(PocketModule):
    """
    Lifecycle wrapper for the structured logger.
    start() initialises the log file and rotation handler.
    stop() flushes and closes the handler cleanly.
    health_check() confirms the log file is writable.
    on_event() handles bus events that should be logged automatically.
    """

    def start(self) -> None:
        log.init()
        log.info("logger", "Structured logging started")

    def stop(self) -> None:
        log.info("logger", "Structured logging stopping")
        if log._handler:
            try:
                log._handler.close()
            except Exception:
                pass

    def health_check(self) -> bool:
        try:
            if not log._ready:
                return False
            if not log._log_path:
                return False
            # Confirm we can write
            log._write({"type": "health_check", "module": "logger"})
            return True
        except Exception as e:
            print(f"  [LoggerModule] health_check error: {e}")
            return False

    def on_event(self, event: dict) -> None:
        """Auto-log bus events that are worth keeping."""
        etype = event.get("type", "")

        if etype == "connection.websocket.connected":
            log.websocket("CONNECTED", attempt=event.get("attempt", 0))

        elif etype == "connection.websocket.disconnected":
            log.websocket("DISCONNECTED",
                          attempt=event.get("attempt", 0),
                          reason=event.get("reason"))

        elif etype == "connection.websocket.reconnecting":
            log.websocket("RECONNECTING", attempt=event.get("attempt", 0))

        elif etype == "connection.websocket.degraded":
            log.websocket("DEGRADED_MODE",
                          attempt=event.get("attempts", 0),
                          reason=event.get("reason"))

        elif etype == "executor.run":
            # command logging happens inside execute_command() after approval
            pass


# Singletons
log = StructuredLogger()
logger_module = LoggerModule()