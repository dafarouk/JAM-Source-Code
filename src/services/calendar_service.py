from __future__ import annotations

from datetime import datetime

from database import connection, utc_now


class CalendarService:
    VALID_TYPES = {
        "Interview",
        "Follow-up",
        "Deadline",
        "Reminder",
        "Other",
    }

    def _normalize_event_type(self, value: str | None) -> str:
        event_type = str(value or "Reminder").strip()
        if event_type not in self.VALID_TYPES:
            raise ValueError("Unsupported calendar event type.")
        return event_type

    def _normalize_event_at(self, value: str | None) -> str:
        raw = str(value or "").strip()
        if not raw:
            raise ValueError("Choose a date and time for the calendar event.")

        try:
            parsed = datetime.fromisoformat(raw)
        except ValueError as exc:
            raise ValueError("Invalid calendar event date/time.") from exc

        return parsed.isoformat(timespec="minutes")

    def _normalize_application_id(self, value) -> int | None:
        if value in (None, "", 0, "0"):
            return None

        try:
            application_id = int(value)
        except (TypeError, ValueError) as exc:
            raise ValueError("Invalid application link for calendar event.") from exc

        with connection() as conn:
            exists = conn.execute(
                "SELECT 1 FROM applications WHERE id = ?",
                (application_id,),
            ).fetchone()

        if not exists:
            raise ValueError("The linked application no longer exists.")

        return application_id

    def list_all(self) -> list[dict]:
        with connection() as conn:
            rows = conn.execute(
                """
                SELECT
                    e.*,
                    a.company AS application_company,
                    a.job_title AS application_job_title,
                    a.status AS application_status
                FROM calendar_events e
                LEFT JOIN applications a ON a.id = e.application_id
                ORDER BY datetime(e.event_at) ASC, e.id ASC
                """
            ).fetchall()

        return [dict(row) for row in rows]

    def get(self, event_id: int) -> dict | None:
        with connection() as conn:
            row = conn.execute(
                """
                SELECT
                    e.*,
                    a.company AS application_company,
                    a.job_title AS application_job_title,
                    a.status AS application_status
                FROM calendar_events e
                LEFT JOIN applications a ON a.id = e.application_id
                WHERE e.id = ?
                """,
                (int(event_id),),
            ).fetchone()

        return dict(row) if row else None

    def save(self, payload: dict) -> dict:
        payload = payload or {}
        event_id = payload.get("id")
        event_type = self._normalize_event_type(payload.get("event_type"))
        event_at = self._normalize_event_at(payload.get("event_at"))
        application_id = self._normalize_application_id(payload.get("application_id"))
        title = str(payload.get("title") or "").strip() or event_type
        notes = str(payload.get("notes") or "").strip()
        location = str(payload.get("location") or "").strip()
        completed = 1 if payload.get("completed") in (True, 1, "1", "true", "True") else 0
        now = utc_now()

        with connection() as conn:
            if event_id:
                current = conn.execute(
                    "SELECT id, created_at FROM calendar_events WHERE id = ?",
                    (int(event_id),),
                ).fetchone()
                if not current:
                    raise ValueError("Calendar event not found.")

                conn.execute(
                    """
                    UPDATE calendar_events
                    SET application_id = ?, event_type = ?, title = ?, event_at = ?,
                        notes = ?, location = ?, completed = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (
                        application_id,
                        event_type,
                        title,
                        event_at,
                        notes,
                        location,
                        completed,
                        now,
                        int(event_id),
                    ),
                )
                saved_id = int(event_id)
            else:
                cursor = conn.execute(
                    """
                    INSERT INTO calendar_events(
                        application_id,
                        event_type,
                        title,
                        event_at,
                        notes,
                        location,
                        completed,
                        created_at,
                        updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        application_id,
                        event_type,
                        title,
                        event_at,
                        notes,
                        location,
                        completed,
                        now,
                        now,
                    ),
                )
                saved_id = int(cursor.lastrowid)

        item = self.get(saved_id)
        if not item:
            raise RuntimeError("Calendar event could not be loaded after saving.")
        return item

    def set_completed(self, event_id: int, completed: bool) -> dict:
        now = utc_now()
        with connection() as conn:
            cursor = conn.execute(
                "UPDATE calendar_events SET completed = ?, updated_at = ? WHERE id = ?",
                (1 if completed else 0, now, int(event_id)),
            )
            if cursor.rowcount < 1:
                raise ValueError("Calendar event not found.")

        item = self.get(int(event_id))
        if not item:
            raise RuntimeError("Calendar event could not be loaded after updating.")
        return item

    def delete(self, event_id: int) -> bool:
        with connection() as conn:
            cursor = conn.execute(
                "DELETE FROM calendar_events WHERE id = ?",
                (int(event_id),),
            )
        return cursor.rowcount > 0
