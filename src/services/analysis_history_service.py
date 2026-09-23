from __future__ import annotations

import json
from typing import Any

from database import connection, init_database, utc_now


class AnalysisHistoryService:
    """Persist manually saved Analyzer runs in JAM's local SQLite database."""

    def __init__(self) -> None:
        init_database()

    def save(
        self,
        job_title: str,
        description: str,
        analysis: dict[str, Any],
    ) -> dict:
        title = str(job_title or "").strip()
        description = str(description or "").strip()

        if not title and not description:
            raise ValueError("Add a job title or description before saving the analysis.")

        score = analysis.get("score")
        score_value = int(score) if score is not None else None
        score_label = str(analysis.get("score_label") or "")
        payload = json.dumps(analysis, ensure_ascii=False)
        created_at = utc_now()

        with connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO analyzer_history(
                    job_title,
                    description,
                    score,
                    score_label,
                    analysis_json,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    title,
                    description,
                    score_value,
                    score_label,
                    payload,
                    created_at,
                ),
            )
            row_id = int(cursor.lastrowid)

        return self.get(row_id)

    def get(self, history_id: int) -> dict:
        with connection() as conn:
            row = conn.execute(
                "SELECT * FROM analyzer_history WHERE id = ?",
                (int(history_id),),
            ).fetchone()

        if row is None:
            raise ValueError("Saved analysis not found.")

        return self._row_to_dict(row)

    def list(self, limit: int = 50) -> list[dict]:
        limit = max(1, min(200, int(limit or 50)))

        with connection() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM analyzer_history
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [self._row_to_dict(row) for row in rows]

    def delete(self, history_id: int) -> bool:
        with connection() as conn:
            cursor = conn.execute(
                "DELETE FROM analyzer_history WHERE id = ?",
                (int(history_id),),
            )

        return cursor.rowcount > 0

    @staticmethod
    def _row_to_dict(row) -> dict:
        try:
            analysis = json.loads(row["analysis_json"] or "{}")
        except Exception:
            analysis = {}

        return {
            "id": int(row["id"]),
            "job_title": row["job_title"] or "",
            "description": row["description"] or "",
            "score": row["score"],
            "score_label": row["score_label"] or "",
            "analysis": analysis,
            "created_at": row["created_at"] or "",
        }
