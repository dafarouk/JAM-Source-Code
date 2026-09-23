from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Iterator

from config import DB_PATH, ensure_runtime_dirs

SCHEMA_VERSION = 5


def utc_now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


@contextmanager
def connection() -> Iterator[sqlite3.Connection]:
    ensure_runtime_dirs()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _columns(conn: sqlite3.Connection, table: str) -> set[str]:
    return {
        str(row["name"])
        for row in conn.execute(f"PRAGMA table_info({table})").fetchall()
    }


def _ensure_column(
    conn: sqlite3.Connection,
    table: str,
    name: str,
    definition: str,
) -> None:
    if name not in _columns(conn, table):
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {definition}")


def init_database() -> None:
    with connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS schema_meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company TEXT NOT NULL DEFAULT '',
                job_title TEXT NOT NULL DEFAULT '',
                description TEXT NOT NULL DEFAULT '',
                url TEXT NOT NULL DEFAULT '',
                location TEXT NOT NULL DEFAULT '',
                work_mode TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'Saved',
                rating INTEGER NOT NULL DEFAULT 0 CHECK(rating BETWEEN 0 AND 5),
                notes TEXT NOT NULL DEFAULT '',
                contact_name TEXT NOT NULL DEFAULT '',
                contact_url TEXT NOT NULL DEFAULT '',
                source TEXT NOT NULL DEFAULT '',
                salary_text TEXT NOT NULL DEFAULT '',
                salary_min REAL,
                salary_max REAL,
                salary_currency TEXT NOT NULL DEFAULT '',
                salary_period TEXT NOT NULL DEFAULT '',
                salary_basis TEXT NOT NULL DEFAULT '',
                date_saved TEXT NOT NULL,
                date_applied TEXT,
                updated_at TEXT NOT NULL,
                match_score INTEGER,
                analysis_json TEXT NOT NULL DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS application_status_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                application_id INTEGER NOT NULL,
                status TEXT NOT NULL,
                changed_at TEXT NOT NULL,
                FOREIGN KEY(application_id) REFERENCES applications(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS export_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                export_type TEXT NOT NULL,
                path TEXT NOT NULL,
                row_count INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS recent_projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                last_opened_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS analyzer_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_title TEXT NOT NULL DEFAULT '',
                description TEXT NOT NULL DEFAULT '',
                score INTEGER,
                score_label TEXT NOT NULL DEFAULT '',
                analysis_json TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS saved_views (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                state_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );


            CREATE TABLE IF NOT EXISTS application_contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                application_id INTEGER NOT NULL,
                name TEXT NOT NULL DEFAULT '',
                url TEXT NOT NULL DEFAULT '',
                email TEXT NOT NULL DEFAULT '',
                phone TEXT NOT NULL DEFAULT '',
                role TEXT NOT NULL DEFAULT '',
                note TEXT NOT NULL DEFAULT '',
                is_primary INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(application_id) REFERENCES applications(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS application_notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                application_id INTEGER NOT NULL,
                note_text TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(application_id) REFERENCES applications(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS application_attachments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                application_id INTEGER NOT NULL,
                file_name TEXT NOT NULL DEFAULT '',
                stored_path TEXT NOT NULL DEFAULT '',
                category TEXT NOT NULL DEFAULT 'Other',
                created_at TEXT NOT NULL,
                FOREIGN KEY(application_id) REFERENCES applications(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS calendar_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                application_id INTEGER,
                event_type TEXT NOT NULL DEFAULT 'Reminder',
                title TEXT NOT NULL DEFAULT '',
                event_at TEXT NOT NULL,
                notes TEXT NOT NULL DEFAULT '',
                location TEXT NOT NULL DEFAULT '',
                completed INTEGER NOT NULL DEFAULT 0 CHECK(completed IN (0, 1)),
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(application_id) REFERENCES applications(id) ON DELETE CASCADE
            );
            """
        )

        # Safe in-place upgrade for databases created before Batch 2.
        _ensure_column(conn, "applications", "salary_min", "REAL")
        _ensure_column(conn, "applications", "salary_max", "REAL")
        _ensure_column(conn, "applications", "salary_currency", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(conn, "applications", "salary_period", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(conn, "applications", "salary_basis", "TEXT NOT NULL DEFAULT ''")

        # Batch 3 migration: preserve the old single contact / notes fields as
        # the first entries of the richer tracking history. The NOT EXISTS
        # checks keep the migration idempotent on every JAM launch.
        conn.execute(
            "INSERT INTO application_contacts("
            "application_id, name, url, email, phone, role, note, is_primary, created_at, updated_at"
            ") "
            "SELECT a.id, a.contact_name, a.contact_url, '', '', '', '', 1, a.date_saved, a.updated_at "
            "FROM applications a "
            "WHERE (TRIM(a.contact_name) <> '' OR TRIM(a.contact_url) <> '') "
            "AND NOT EXISTS ("
            "SELECT 1 FROM application_contacts c WHERE c.application_id = a.id AND c.is_primary = 1"
            ")"
        )
        conn.execute(
            "INSERT INTO application_notes(application_id, note_text, created_at, updated_at) "
            "SELECT a.id, a.notes, a.date_saved, a.updated_at "
            "FROM applications a "
            "WHERE TRIM(a.notes) <> '' "
            "AND NOT EXISTS ("
            "SELECT 1 FROM application_notes n WHERE n.application_id = a.id"
            ")"
        )

        conn.execute(
            "INSERT INTO schema_meta(key, value) VALUES('schema_version', ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (str(SCHEMA_VERSION),),
        )


def reset_database_data() -> None:
    with connection() as conn:
        conn.execute("DELETE FROM calendar_events")
        conn.execute("DELETE FROM application_contacts")
        conn.execute("DELETE FROM application_notes")
        conn.execute("DELETE FROM application_attachments")
        conn.execute("DELETE FROM application_status_history")
        conn.execute("DELETE FROM applications")
        conn.execute("DELETE FROM export_history")
        conn.execute("DELETE FROM recent_projects")
        conn.execute("DELETE FROM saved_views")
        conn.execute("DELETE FROM settings")
        conn.execute("DELETE FROM analyzer_history")
        conn.execute(
            "DELETE FROM sqlite_sequence WHERE name IN "
            "('applications','application_status_history','export_history',"
            "'recent_projects','analyzer_history','saved_views','application_contacts',"
            "'application_notes','application_attachments','calendar_events')"
        )
