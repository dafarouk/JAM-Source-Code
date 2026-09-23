from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Iterable

from database import connection, utc_now
from services.url_utils import normalize_job_url

STATUSES_THAT_IMPLY_APPLIED = {
    "Applied", "Interviewing", "Offer", "Accepted", "Rejected", "Withdrawn"
}


def _norm(value) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").lower()).strip()


def _number(value):
    if value is None or str(value).strip() == "":
        return None
    try:
        return float(str(value).replace(",", "."))
    except Exception:
        return None


class ApplicationRepository:
    FIELDS = (
        "company", "job_title", "description", "url", "location", "work_mode", "status",
        "rating", "notes", "contact_name", "contact_url", "source", "salary_text",
        "salary_min", "salary_max", "salary_currency", "salary_period", "salary_basis",
        "date_saved", "date_applied", "updated_at", "match_score", "analysis_json",
    )

    def list_all(self) -> list[dict]:
        with connection() as conn:
            rows = conn.execute(
                "SELECT * FROM applications ORDER BY datetime(date_saved) DESC, id DESC"
            ).fetchall()
        return [dict(row) for row in rows]

    def get(self, application_id: int) -> dict | None:
        with connection() as conn:
            row = conn.execute(
                "SELECT * FROM applications WHERE id = ?", (application_id,)
            ).fetchone()
        return dict(row) if row else None

    def status_history(self, application_id: int) -> list[dict]:
        with connection() as conn:
            rows = conn.execute(
                "SELECT id, application_id, status, changed_at "
                "FROM application_status_history WHERE application_id = ? "
                "ORDER BY datetime(changed_at), id",
                (int(application_id),),
            ).fetchall()
        return [dict(row) for row in rows]

    def details(self, application_id: int) -> dict | None:
        app = self.get(application_id)
        if not app:
            return None
        try:
            app["analysis"] = json.loads(app.get("analysis_json") or "{}")
        except Exception:
            app["analysis"] = {}
        app["status_history"] = self.status_history(application_id)
        return app

    def find_duplicates(
        self,
        payload: dict,
        exclude_id: int | None = None,
    ) -> list[dict]:
        company = _norm(payload.get("company"))
        title = _norm(payload.get("job_title"))
        url = normalize_job_url(payload.get("url"))
        exclude = int(exclude_id) if exclude_id else None

        matches = []
        for row in self.list_all():
            if exclude and int(row["id"]) == exclude:
                continue

            row_url = normalize_job_url(row.get("url"))
            same_url = bool(url and row_url and url == row_url)
            same_identity = bool(
                company and title
                and company == _norm(row.get("company"))
                and title == _norm(row.get("job_title"))
            )
            if same_url or same_identity:
                item = dict(row)
                item["duplicate_reason"] = (
                    "Same normalized job URL" if same_url else "Same company and job title"
                )
                matches.append(item)
        return matches[:10]

    def create(self, payload: dict) -> dict:
        now = utc_now()
        status = str(payload.get("status") or "Saved")
        date_saved = str(payload.get("date_saved") or now)
        date_applied = payload.get("date_applied")
        if not date_applied and status in STATUSES_THAT_IMPLY_APPLIED:
            date_applied = now

        data = {
            "company": str(payload.get("company") or "").strip(),
            "job_title": str(payload.get("job_title") or "").strip(),
            "description": str(payload.get("description") or "").strip(),
            "url": normalize_job_url(payload.get("url")),
            "location": str(payload.get("location") or "").strip(),
            "work_mode": str(payload.get("work_mode") or "").strip(),
            "status": status,
            "rating": max(0, min(5, int(payload.get("rating") or 0))),
            "notes": str(payload.get("notes") or "").strip(),
            "contact_name": str(payload.get("contact_name") or "").strip(),
            "contact_url": str(payload.get("contact_url") or "").strip(),
            "source": str(payload.get("source") or "").strip(),
            "salary_text": str(payload.get("salary_text") or "").strip(),
            "salary_min": _number(payload.get("salary_min")),
            "salary_max": _number(payload.get("salary_max")),
            "salary_currency": str(payload.get("salary_currency") or "").strip().upper(),
            "salary_period": str(payload.get("salary_period") or "").strip(),
            "salary_basis": str(payload.get("salary_basis") or "").strip(),
            "date_saved": date_saved,
            "date_applied": date_applied,
            "updated_at": now,
            "match_score": payload.get("match_score"),
            "analysis_json": str(payload.get("analysis_json") or ""),
        }
        columns = ", ".join(data.keys())
        placeholders = ", ".join("?" for _ in data)
        with connection() as conn:
            cursor = conn.execute(
                f"INSERT INTO applications ({columns}) VALUES ({placeholders})",
                tuple(data.values()),
            )
            application_id = int(cursor.lastrowid)
            conn.execute(
                "INSERT INTO application_status_history(application_id, status, changed_at) "
                "VALUES (?, ?, ?)",
                (application_id, status, now),
            )
        return self.get(application_id) or {}

    def update(self, application_id: int, payload: dict) -> dict:
        current = self.get(application_id)
        if not current:
            raise ValueError("Application not found.")
        now = utc_now()
        status = str(payload.get("status", current["status"]) or "Saved")
        date_applied = payload.get("date_applied", current["date_applied"])
        if not date_applied and status in STATUSES_THAT_IMPLY_APPLIED:
            date_applied = now

        data = {}
        payload = dict(payload)
        if "url" in payload:
            payload["url"] = normalize_job_url(payload.get("url"))

        for field in self.FIELDS:
            if field in ("updated_at", "date_applied"):
                continue
            if field in payload:
                data[field] = payload[field]

        if "rating" in data:
            data["rating"] = max(0, min(5, int(data["rating"] or 0)))
        for field in ("salary_min", "salary_max"):
            if field in data:
                data[field] = _number(data[field])
        if "salary_currency" in data:
            data["salary_currency"] = str(data["salary_currency"] or "").strip().upper()

        data["status"] = status
        data["date_applied"] = date_applied
        data["updated_at"] = now

        assignments = ", ".join(f"{key} = ?" for key in data)
        values = list(data.values()) + [application_id]
        with connection() as conn:
            conn.execute(f"UPDATE applications SET {assignments} WHERE id = ?", values)
            if status != current["status"]:
                conn.execute(
                    "INSERT INTO application_status_history(application_id, status, changed_at) "
                    "VALUES (?, ?, ?)",
                    (application_id, status, now),
                )
        return self.get(application_id) or {}

    def bulk_update(self, application_ids: Iterable[int], payload: dict) -> list[dict]:
        ids = [int(value) for value in application_ids]
        if not ids:
            return []
        allowed = {"status", "source", "rating"}
        update_payload = {key: value for key, value in payload.items() if key in allowed}
        if not update_payload:
            raise ValueError("No supported bulk changes were provided.")
        result = []
        for application_id in ids:
            result.append(self.update(application_id, update_payload))
        return result

    def set_analysis(self, application_id: int, score: int | None, analysis: dict) -> None:
        with connection() as conn:
            conn.execute(
                "UPDATE applications SET match_score = ?, analysis_json = ?, updated_at = ? WHERE id = ?",
                (score, json.dumps(analysis, ensure_ascii=False), utc_now(), application_id),
            )

    def delete(self, application_id: int) -> None:
        with connection() as conn:
            conn.execute("DELETE FROM applications WHERE id = ?", (application_id,))

    def delete_many(self, application_ids: Iterable[int]) -> int:
        ids = [int(value) for value in application_ids]
        if not ids:
            return 0
        placeholders = ",".join("?" for _ in ids)
        with connection() as conn:
            cursor = conn.execute(f"DELETE FROM applications WHERE id IN ({placeholders})", ids)
            return cursor.rowcount

    def get_many(self, application_ids: Iterable[int] | None = None) -> list[dict]:
        ids = [int(value) for value in (application_ids or [])]
        if not ids:
            return self.list_all()
        placeholders = ",".join("?" for _ in ids)
        with connection() as conn:
            rows = conn.execute(
                f"SELECT * FROM applications WHERE id IN ({placeholders}) "
                "ORDER BY datetime(date_saved) DESC, id DESC",
                ids,
            ).fetchall()
        return [dict(row) for row in rows]

    def stats(self) -> dict:
        rows = self.list_all()
        total = len(rows)
        applied = sum(1 for row in rows if row.get("date_applied"))
        interviewing = sum(1 for row in rows if row["status"] == "Interviewing")
        accepted = sum(1 for row in rows if row["status"] in {"Accepted", "Offer"})
        rejected = sum(1 for row in rows if row["status"] == "Rejected")
        scores = [int(row["match_score"]) for row in rows if row.get("match_score") is not None]
        avg_score = round(sum(scores) / len(scores), 1) if scores else 0

        average_per_day = 0.0
        if rows:
            parsed_dates = []
            for row in rows:
                try:
                    parsed_dates.append(datetime.fromisoformat(row["date_saved"]).date())
                except Exception:
                    pass
            if parsed_dates:
                span = max(1, (datetime.now().date() - min(parsed_dates)).days + 1)
                average_per_day = round(total / span, 2)

        return {
            "total": total,
            "applied": applied,
            "interviewing": interviewing,
            "accepted": accepted,
            "rejected": rejected,
            "average_per_day": average_per_day,
            "average_match_score": avg_score,
        }
