from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from config import APP_VERSION, RECOVERY_DIR, ensure_runtime_dirs
from database import connection, utc_now


class ProjectService:
    FORMAT = "JAM_PROJECT"
    FORMAT_VERSION = 3
    RECOVERY_FORMAT = "JAM_PROJECT_RECOVERY"

    def __init__(self) -> None:
        ensure_runtime_dirs()
        self._current_path: Path | None = None
        self._dirty = False
        self._recovery_path = RECOVERY_DIR / "project_recovery.json"

    @property
    def current_path(self) -> str:
        return str(self._current_path) if self._current_path else ""

    @property
    def dirty(self) -> bool:
        return bool(self._dirty and self._current_path)

    def snapshot(self) -> dict:
        with connection() as conn:
            applications = [
                dict(row)
                for row in conn.execute(
                    "SELECT * FROM applications ORDER BY id"
                ).fetchall()
            ]
            status_history = [
                dict(row)
                for row in conn.execute(
                    "SELECT * FROM application_status_history ORDER BY id"
                ).fetchall()
            ]
            settings = {
                row["key"]: row["value"]
                for row in conn.execute(
                    "SELECT key, value FROM settings WHERE key != ?",
                    ("tutorial_completed",),
                ).fetchall()
            }
            saved_views = [
                dict(row)
                for row in conn.execute(
                    "SELECT * FROM saved_views ORDER BY id"
                ).fetchall()
            ]
            contacts = [
                dict(row)
                for row in conn.execute(
                    "SELECT * FROM application_contacts ORDER BY id"
                ).fetchall()
            ]
            notes = [
                dict(row)
                for row in conn.execute(
                    "SELECT * FROM application_notes ORDER BY id"
                ).fetchall()
            ]
            attachments = [
                dict(row)
                for row in conn.execute(
                    "SELECT * FROM application_attachments ORDER BY id"
                ).fetchall()
            ]
            calendar_events = [
                dict(row)
                for row in conn.execute(
                    "SELECT * FROM calendar_events ORDER BY id"
                ).fetchall()
            ]

        return {
            "format": self.FORMAT,
            "format_version": self.FORMAT_VERSION,
            "jam_version": APP_VERSION,
            "saved_at": utc_now(),
            "applications": applications,
            "status_history": status_history,
            "settings": settings,
            "saved_views": saved_views,
            "contacts": contacts,
            "notes_history": notes,
            "attachments": attachments,
            "calendar_events": calendar_events,
        }

    def _apply_snapshot(self, data: dict) -> int:
        if data.get("format") != self.FORMAT:
            raise ValueError("This file is not a valid JAM project.")

        applications = data.get("applications", [])
        status_history = data.get("status_history", [])
        settings = data.get("settings", {})
        saved_views = data.get("saved_views", [])
        contacts = data.get("contacts", [])
        notes_history = data.get("notes_history", [])
        attachments = data.get("attachments", [])
        calendar_events = data.get("calendar_events", [])

        with connection() as conn:
            local_tutorial_row = conn.execute(
                "SELECT value FROM settings WHERE key = ?",
                ("tutorial_completed",),
            ).fetchone()
            local_tutorial_completed = (
                local_tutorial_row["value"]
                if local_tutorial_row
                else None
            )

            conn.execute("DELETE FROM calendar_events")
            conn.execute("DELETE FROM application_contacts")
            conn.execute("DELETE FROM application_notes")
            conn.execute("DELETE FROM application_attachments")
            conn.execute("DELETE FROM application_status_history")
            conn.execute("DELETE FROM applications")
            conn.execute("DELETE FROM settings")
            conn.execute("DELETE FROM saved_views")

            app_columns = (
                "id",
                "company",
                "job_title",
                "description",
                "url",
                "location",
                "work_mode",
                "status",
                "rating",
                "notes",
                "contact_name",
                "contact_url",
                "source",
                "salary_text",
                "salary_min",
                "salary_max",
                "salary_currency",
                "salary_period",
                "salary_basis",
                "date_saved",
                "date_applied",
                "updated_at",
                "match_score",
                "analysis_json",
            )

            app_defaults = {
                "company": "",
                "job_title": "",
                "description": "",
                "url": "",
                "location": "",
                "work_mode": "",
                "status": "Saved",
                "rating": 0,
                "notes": "",
                "contact_name": "",
                "contact_url": "",
                "source": "",
                "salary_text": "",
                "salary_min": None,
                "salary_max": None,
                "salary_currency": "",
                "salary_period": "",
                "salary_basis": "",
                "date_saved": utc_now(),
                "date_applied": None,
                "updated_at": utc_now(),
                "match_score": None,
                "analysis_json": "",
            }

            for row in applications:
                values = [row.get(column, app_defaults.get(column)) for column in app_columns]
                placeholders = ",".join("?" for _ in app_columns)
                conn.execute(
                    f"INSERT INTO applications ({','.join(app_columns)}) VALUES ({placeholders})",
                    values,
                )

            history_columns = (
                "id",
                "application_id",
                "status",
                "changed_at",
            )

            for row in status_history:
                values = [row.get(column) for column in history_columns]
                placeholders = ",".join("?" for _ in history_columns)
                conn.execute(
                    f"INSERT INTO application_status_history ({','.join(history_columns)}) VALUES ({placeholders})",
                    values,
                )

            for key, value in settings.items():
                conn.execute(
                    "INSERT INTO settings(key, value) VALUES (?, ?)",
                    (key, str(value)),
                )

            if local_tutorial_completed is not None:
                conn.execute(
                    "INSERT INTO settings(key, value) VALUES (?, ?)",
                    ("tutorial_completed", str(local_tutorial_completed)),
                )

            for view in saved_views:
                conn.execute(
                    "INSERT INTO saved_views(id, name, state_json, created_at, updated_at) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (
                        view.get("id"),
                        view.get("name", "View"),
                        view.get("state_json", "{}"),
                        view.get("created_at", utc_now()),
                        view.get("updated_at", utc_now()),
                    ),
                )

            for item in contacts:
                conn.execute(
                    "INSERT INTO application_contacts(" 
                    "id, application_id, name, url, email, phone, role, note, is_primary, created_at, updated_at" 
                    ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        item.get("id"), item.get("application_id"), item.get("name", ""),
                        item.get("url", ""), item.get("email", ""), item.get("phone", ""),
                        item.get("role", ""), item.get("note", ""), int(item.get("is_primary") or 0),
                        item.get("created_at", utc_now()), item.get("updated_at", utc_now()),
                    ),
                )

            for item in notes_history:
                conn.execute(
                    "INSERT INTO application_notes(id, application_id, note_text, created_at, updated_at) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (
                        item.get("id"), item.get("application_id"), item.get("note_text", ""),
                        item.get("created_at", utc_now()), item.get("updated_at", utc_now()),
                    ),
                )

            for item in attachments:
                conn.execute(
                    "INSERT INTO application_attachments(id, application_id, file_name, stored_path, category, created_at) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        item.get("id"), item.get("application_id"), item.get("file_name", ""),
                        item.get("stored_path", ""), item.get("category", "Other"),
                        item.get("created_at", utc_now()),
                    ),
                )

            for item in calendar_events:
                conn.execute(
                    "INSERT INTO calendar_events("
                    "id, application_id, event_type, title, event_at, notes, location, completed, created_at, updated_at"
                    ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        item.get("id"),
                        item.get("application_id"),
                        item.get("event_type", "Reminder"),
                        item.get("title", ""),
                        item.get("event_at", utc_now()),
                        item.get("notes", ""),
                        item.get("location", ""),
                        int(item.get("completed") or 0),
                        item.get("created_at", utc_now()),
                        item.get("updated_at", utc_now()),
                    ),
                )

            # Backward compatibility for Batch 1/2 .jam files: promote the
            # old single contact / note fields into Batch 3 history when the
            # project did not contain the new collections yet.
            if not contacts:
                conn.execute(
                    "INSERT INTO application_contacts("
                    "application_id, name, url, email, phone, role, note, is_primary, created_at, updated_at"
                    ") "
                    "SELECT id, contact_name, contact_url, '', '', '', '', 1, date_saved, updated_at "
                    "FROM applications WHERE TRIM(contact_name) <> '' OR TRIM(contact_url) <> ''"
                )
            if not notes_history:
                conn.execute(
                    "INSERT INTO application_notes(application_id, note_text, created_at, updated_at) "
                    "SELECT id, notes, date_saved, updated_at FROM applications WHERE TRIM(notes) <> ''"
                )

        return len(applications)

    def save(self, path_value: str) -> str:
        path = Path(path_value)
        if path.suffix.lower() != ".jam":
            path = path.with_suffix(".jam")

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                self.snapshot(),
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        self._current_path = path.resolve()
        self._dirty = False
        self.discard_recovery()
        self.track_recent(path)
        return str(path)

    def save_current(self) -> str:
        if not self._current_path:
            raise ValueError("No active .jam project to save.")
        return self.save(str(self._current_path))

    def load(self, path_value: str) -> dict:
        path = Path(path_value)
        data = json.loads(path.read_text(encoding="utf-8"))
        count = self._apply_snapshot(data)

        self._current_path = path.resolve()
        self._dirty = False
        self.discard_recovery()
        self.track_recent(path)

        return {
            "path": str(path),
            "applications": count,
        }

    def mark_dirty(self) -> None:
        if not self._current_path:
            return

        self._dirty = True
        self.write_recovery()

    def write_recovery(self) -> dict | None:
        if not self._current_path:
            return None

        payload = {
            "format": self.RECOVERY_FORMAT,
            "saved_at": utc_now(),
            "current_project_path": str(self._current_path),
            "snapshot": self.snapshot(),
        }

        temp = self._recovery_path.with_suffix(".tmp")
        temp.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temp.replace(self._recovery_path)
        return payload

    def recovery_info(self) -> dict | None:
        if not self._recovery_path.exists():
            return None

        try:
            data = json.loads(
                self._recovery_path.read_text(encoding="utf-8")
            )
            if data.get("format") != self.RECOVERY_FORMAT:
                return None

            snapshot = data.get("snapshot") or {}
            return {
                "saved_at": data.get("saved_at", ""),
                "current_project_path": data.get("current_project_path", ""),
                "application_count": len(snapshot.get("applications") or []),
            }
        except Exception:
            return None

    def restore_recovery(self) -> dict:
        if not self._recovery_path.exists():
            raise FileNotFoundError("No recovered .jam project changes were found.")

        data = json.loads(
            self._recovery_path.read_text(encoding="utf-8")
        )
        if data.get("format") != self.RECOVERY_FORMAT:
            raise ValueError("The project recovery file is invalid.")

        snapshot = data.get("snapshot") or {}
        count = self._apply_snapshot(snapshot)

        current = str(data.get("current_project_path") or "").strip()
        self._current_path = Path(current).resolve() if current else None
        self._dirty = bool(self._current_path)

        return {
            "path": self.current_path,
            "applications": count,
            "dirty": self.dirty,
        }

    def discard_recovery(self) -> None:
        try:
            self._recovery_path.unlink(missing_ok=True)
        except Exception:
            pass

    def discard_dirty_state(self) -> None:
        self._dirty = False
        self.discard_recovery()

    def clear_active_project(self) -> None:
        self._current_path = None
        self._dirty = False
        self.discard_recovery()

    def state(self) -> dict:
        return {
            "current_path": self.current_path,
            "dirty": self.dirty,
            "recovery": self.recovery_info(),
        }

    def track_recent(self, path: Path) -> None:
        with connection() as conn:
            conn.execute(
                "INSERT INTO recent_projects(path, name, last_opened_at) VALUES (?, ?, ?) "
                "ON CONFLICT(path) DO UPDATE SET name=excluded.name, last_opened_at=excluded.last_opened_at",
                (str(path), path.stem, utc_now()),
            )

    def recent(self, limit: int = 8) -> list[dict]:
        with connection() as conn:
            rows = conn.execute(
                "SELECT * FROM recent_projects ORDER BY datetime(last_opened_at) DESC, id DESC LIMIT ?",
                (limit,),
            ).fetchall()

        result = []
        for row in rows:
            item = dict(row)
            path = Path(item["path"])
            item["exists"] = path.exists()
            item["modified_at"] = None
            item["application_count"] = None
            if path.exists():
                try:
                    stat = path.stat()
                    item["modified_at"] = datetime.fromtimestamp(stat.st_mtime).astimezone().isoformat(timespec="seconds")
                except Exception:
                    pass
                try:
                    data = json.loads(path.read_text(encoding="utf-8"))
                    item["application_count"] = len(data.get("applications") or [])
                except Exception:
                    pass
            result.append(item)

        return result

    def remove_recent(self, path_value: str) -> bool:
        with connection() as conn:
            cursor = conn.execute(
                "DELETE FROM recent_projects WHERE path = ?",
                (str(path_value),),
            )
            return cursor.rowcount > 0

