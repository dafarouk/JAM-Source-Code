from __future__ import annotations

import shutil
import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path

from config import BACKUP_DIR, DB_PATH, ensure_runtime_dirs
from database import init_database


class BackupService:
    def _validate_database(self, path: Path) -> None:
        if not path.exists() or not path.is_file():
            raise FileNotFoundError("Backup file does not exist.")

        try:
            # sqlite3.Connection's own context manager commits/rolls back but
            # does NOT close the connection. On Windows that can leave the DB
            # file locked and break os.replace/unlink. closing() guarantees the
            # file handle is released before restore continues.
            with closing(sqlite3.connect(path)) as conn:
                tables = {
                    row[0]
                    for row in conn.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    ).fetchall()
                }
        except Exception as exc:
            raise ValueError(
                "The selected file is not a readable SQLite database."
            ) from exc

        required = {"applications", "settings"}
        missing = required - tables
        if missing:
            raise ValueError(
                "The selected backup is not a valid JAM database. Missing: "
                + ", ".join(sorted(missing))
            )

    def create_backup(self, label: str = "manual") -> str:
        ensure_runtime_dirs()
        if not DB_PATH.exists():
            raise FileNotFoundError("JAM database does not exist yet.")

        stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S_%f")
        safe_label = "".join(
            ch if ch.isalnum() or ch in {"-", "_"} else "_"
            for ch in str(label or "manual").strip().lower()
        ) or "manual"

        target = BACKUP_DIR / f"jam_backup_{stamp}_{safe_label}.db"

        # Use SQLite's backup API and explicitly close both connections.
        # This is safe if JAM has the live DB open elsewhere and, crucially,
        # avoids lingering Windows file locks.
        with closing(sqlite3.connect(DB_PATH)) as source:
            with closing(sqlite3.connect(target)) as dest:
                source.backup(dest)

        self._validate_database(target)
        return str(target)

    def list_backups(self) -> list[dict]:
        ensure_runtime_dirs()
        items = []

        for path in sorted(
            BACKUP_DIR.glob("jam_backup_*.db"),
            key=lambda candidate: candidate.stat().st_mtime,
            reverse=True,
        ):
            stat = path.stat()
            items.append(
                {
                    "name": path.name,
                    "path": str(path),
                    "size": stat.st_size,
                    "created_at": datetime.fromtimestamp(stat.st_mtime)
                    .astimezone()
                    .isoformat(timespec="seconds"),
                }
            )

        return items

    def restore_backup(self, path_value: str) -> dict:
        ensure_runtime_dirs()
        backup = Path(path_value).resolve()
        backup_root = BACKUP_DIR.resolve()

        # Restore only JAM-managed backups.
        if backup_root not in backup.parents:
            raise ValueError("JAM can only restore files from its backup folder.")

        self._validate_database(backup)

        # Always preserve the pre-restore state first.
        safety = self.create_backup("before_restore")
        temp = DB_PATH.with_suffix(".restore.tmp")

        try:
            temp.unlink(missing_ok=True)
            shutil.copy2(backup, temp)
            self._validate_database(temp)

            # All validation connections are guaranteed closed at this point,
            # so Windows can atomically replace the live DB file.
            temp.replace(DB_PATH)
            init_database()
        except Exception:
            # Best effort cleanup. Because validation connections are closed,
            # this should not hit WinError 32 anymore.
            try:
                temp.unlink(missing_ok=True)
            except OSError:
                pass

            # Best-effort rollback to the safety copy.
            try:
                shutil.copy2(safety, DB_PATH)
                init_database()
            except Exception:
                pass

            raise

        return {
            "restored": str(backup),
            "safety_backup": safety,
        }
