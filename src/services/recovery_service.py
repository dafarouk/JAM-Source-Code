from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from config import RECOVERY_DIR, ensure_runtime_dirs


class RecoveryService:
    """Small JSON recovery store for unsaved UI drafts."""

    def __init__(self) -> None:
        ensure_runtime_dirs()

    @staticmethod
    def _safe_name(name: str) -> str:
        clean = "".join(ch for ch in str(name) if ch.isalnum() or ch in {"-", "_"})
        if not clean:
            raise ValueError("Invalid recovery draft name.")
        return clean

    def _path(self, name: str) -> Path:
        return RECOVERY_DIR / f"draft_{self._safe_name(name)}.json"

    def save(self, name: str, payload: dict[str, Any]) -> dict:
        path = self._path(name)
        data = {
            "name": self._safe_name(name),
            "saved_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "payload": payload,
        }
        temp = path.with_suffix(".tmp")
        temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        temp.replace(path)
        return data

    def get(self, name: str) -> dict | None:
        path = self._path(name)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(data, dict) or not isinstance(data.get("payload"), dict):
                return None
            return data
        except Exception:
            return None

    def clear(self, name: str) -> None:
        path = self._path(name)
        try:
            path.unlink(missing_ok=True)
        except Exception:
            pass

    def clear_all(self) -> None:
        ensure_runtime_dirs()
        for path in RECOVERY_DIR.glob("draft_*.json"):
            try:
                path.unlink()
            except Exception:
                pass
