from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from config import DEFAULT_APP_DATA_DIR, ensure_runtime_dirs
from database import connection, utc_now


class ApplicationTrackingService:
    """Contacts, note history, and local attachment copies for one application."""

    ATTACHMENTS_DIR = DEFAULT_APP_DATA_DIR / "attachments"

    def __init__(self) -> None:
        ensure_runtime_dirs()
        self.ATTACHMENTS_DIR.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _require_application(application_id: int) -> None:
        with connection() as conn:
            row = conn.execute(
                "SELECT id FROM applications WHERE id = ?",
                (int(application_id),),
            ).fetchone()
        if not row:
            raise ValueError("Application not found.")

    def details(self, application_id: int) -> dict:
        application_id = int(application_id)
        self._require_application(application_id)
        with connection() as conn:
            contacts = [
                dict(row)
                for row in conn.execute(
                    "SELECT * FROM application_contacts WHERE application_id = ? "
                    "ORDER BY is_primary DESC, datetime(created_at), id",
                    (application_id,),
                ).fetchall()
            ]
            notes = [
                dict(row)
                for row in conn.execute(
                    "SELECT * FROM application_notes WHERE application_id = ? "
                    "ORDER BY datetime(created_at) DESC, id DESC",
                    (application_id,),
                ).fetchall()
            ]
            attachments = [
                dict(row)
                for row in conn.execute(
                    "SELECT * FROM application_attachments WHERE application_id = ? "
                    "ORDER BY datetime(created_at) DESC, id DESC",
                    (application_id,),
                ).fetchall()
            ]
        for item in attachments:
            item["exists"] = Path(item.get("stored_path") or "").is_file()
        return {
            "contacts": contacts,
            "notes": notes,
            "attachments": attachments,
        }

    def add_contact(self, application_id: int, payload: dict) -> dict:
        application_id = int(application_id)
        self._require_application(application_id)
        now = utc_now()
        name = str(payload.get("name") or "").strip()
        url = str(payload.get("url") or "").strip()
        email = str(payload.get("email") or "").strip()
        phone = str(payload.get("phone") or "").strip()
        role = str(payload.get("role") or "").strip()
        note = str(payload.get("note") or "").strip()
        if not any((name, url, email, phone)):
            raise ValueError("Add at least a contact name, link, email, or phone.")
        with connection() as conn:
            cursor = conn.execute(
                "INSERT INTO application_contacts("
                "application_id, name, url, email, phone, role, note, is_primary, created_at, updated_at"
                ") VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?)",
                (application_id, name, url, email, phone, role, note, now, now),
            )
            contact_id = int(cursor.lastrowid)
            row = conn.execute(
                "SELECT * FROM application_contacts WHERE id = ?",
                (contact_id,),
            ).fetchone()
        return dict(row)

    def update_contact(self, contact_id: int, payload: dict) -> dict:
        contact_id = int(contact_id)
        fields = {
            "name": str(payload.get("name") or "").strip(),
            "url": str(payload.get("url") or "").strip(),
            "email": str(payload.get("email") or "").strip(),
            "phone": str(payload.get("phone") or "").strip(),
            "role": str(payload.get("role") or "").strip(),
            "note": str(payload.get("note") or "").strip(),
            "updated_at": utc_now(),
        }
        if not any((fields["name"], fields["url"], fields["email"], fields["phone"])):
            raise ValueError("Add at least a contact name, link, email, or phone.")
        with connection() as conn:
            cursor = conn.execute(
                "UPDATE application_contacts SET "
                "name=?, url=?, email=?, phone=?, role=?, note=?, updated_at=? WHERE id=?",
                (*fields.values(), contact_id),
            )
            if not cursor.rowcount:
                raise ValueError("Contact not found.")
            row = conn.execute(
                "SELECT * FROM application_contacts WHERE id = ?",
                (contact_id,),
            ).fetchone()
        return dict(row)

    def delete_contact(self, contact_id: int) -> bool:
        with connection() as conn:
            cursor = conn.execute(
                "DELETE FROM application_contacts WHERE id = ?",
                (int(contact_id),),
            )
            return cursor.rowcount > 0

    def add_note(self, application_id: int, text: str) -> dict:
        application_id = int(application_id)
        self._require_application(application_id)
        value = str(text or "").strip()
        if not value:
            raise ValueError("Note cannot be empty.")
        now = utc_now()
        with connection() as conn:
            cursor = conn.execute(
                "INSERT INTO application_notes(application_id, note_text, created_at, updated_at) "
                "VALUES (?, ?, ?, ?)",
                (application_id, value, now, now),
            )
            note_id = int(cursor.lastrowid)
            row = conn.execute(
                "SELECT * FROM application_notes WHERE id = ?",
                (note_id,),
            ).fetchone()
        return dict(row)

    def update_note(self, note_id: int, text: str) -> dict:
        value = str(text or "").strip()
        if not value:
            raise ValueError("Note cannot be empty.")
        with connection() as conn:
            cursor = conn.execute(
                "UPDATE application_notes SET note_text = ?, updated_at = ? WHERE id = ?",
                (value, utc_now(), int(note_id)),
            )
            if not cursor.rowcount:
                raise ValueError("Note not found.")
            row = conn.execute(
                "SELECT * FROM application_notes WHERE id = ?",
                (int(note_id),),
            ).fetchone()
        return dict(row)

    def delete_note(self, note_id: int) -> bool:
        with connection() as conn:
            cursor = conn.execute(
                "DELETE FROM application_notes WHERE id = ?",
                (int(note_id),),
            )
            return cursor.rowcount > 0

    def add_attachment(self, application_id: int, source_path: str, category: str = "Other") -> dict:
        application_id = int(application_id)
        self._require_application(application_id)
        source = Path(source_path).expanduser().resolve()
        if not source.is_file():
            raise FileNotFoundError(f"Attachment not found: {source}")

        app_dir = self.ATTACHMENTS_DIR / str(application_id)
        app_dir.mkdir(parents=True, exist_ok=True)
        token = uuid.uuid4().hex[:12]
        suffix = source.suffix.lower()
        stored = app_dir / f"{token}{suffix}"
        shutil.copy2(source, stored)

        now = utc_now()
        with connection() as conn:
            cursor = conn.execute(
                "INSERT INTO application_attachments("
                "application_id, file_name, stored_path, category, created_at"
                ") VALUES (?, ?, ?, ?, ?)",
                (
                    application_id,
                    source.name,
                    str(stored),
                    str(category or "Other").strip() or "Other",
                    now,
                ),
            )
            attachment_id = int(cursor.lastrowid)
            row = conn.execute(
                "SELECT * FROM application_attachments WHERE id = ?",
                (attachment_id,),
            ).fetchone()
        item = dict(row)
        item["exists"] = True
        return item

    def delete_attachment(self, attachment_id: int) -> bool:
        attachment_id = int(attachment_id)
        with connection() as conn:
            row = conn.execute(
                "SELECT stored_path FROM application_attachments WHERE id = ?",
                (attachment_id,),
            ).fetchone()
            if not row:
                return False
            conn.execute(
                "DELETE FROM application_attachments WHERE id = ?",
                (attachment_id,),
            )

        try:
            path = Path(row["stored_path"])
            if path.is_file() and self.ATTACHMENTS_DIR in path.resolve().parents:
                path.unlink()
        except Exception:
            pass
        return True
