from __future__ import annotations

import json

from database import connection, utc_now


class SavedViewService:
    def list(self) -> list[dict]:
        with connection() as conn:
            rows = conn.execute(
                "SELECT * FROM saved_views ORDER BY lower(name), id"
            ).fetchall()
        result = []
        for row in rows:
            item = dict(row)
            try:
                item["state"] = json.loads(item.pop("state_json") or "{}")
            except Exception:
                item["state"] = {}
            result.append(item)
        return result

    def save(self, name: str, state: dict) -> dict:
        clean_name = str(name or "").strip()
        if not clean_name:
            raise ValueError("Give this view a name.")
        now = utc_now()
        payload = json.dumps(state or {}, ensure_ascii=False)
        with connection() as conn:
            conn.execute(
                "INSERT INTO saved_views(name, state_json, created_at, updated_at) "
                "VALUES (?, ?, ?, ?) "
                "ON CONFLICT(name) DO UPDATE SET state_json=excluded.state_json, updated_at=excluded.updated_at",
                (clean_name, payload, now, now),
            )
            row = conn.execute(
                "SELECT * FROM saved_views WHERE name = ?", (clean_name,)
            ).fetchone()
        item = dict(row)
        item["state"] = json.loads(item.pop("state_json") or "{}")
        return item

    def rename(self, view_id: int, name: str) -> None:
        clean_name = str(name or "").strip()
        if not clean_name:
            raise ValueError("Give this view a name.")
        with connection() as conn:
            conn.execute(
                "UPDATE saved_views SET name = ?, updated_at = ? WHERE id = ?",
                (clean_name, utc_now(), int(view_id)),
            )

    def delete(self, view_id: int) -> bool:
        with connection() as conn:
            cursor = conn.execute("DELETE FROM saved_views WHERE id = ?", (int(view_id),))
            return cursor.rowcount > 0
