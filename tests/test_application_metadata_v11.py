from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from services.application_metadata_service import (  # noqa: E402
    applicant_competition_color,
    infer_applicant_count,
    normalize_applicant_count,
    normalize_location,
    source_matches,
)


def test_source_aliases_find_company_website() -> None:
    assert "Company Website" in source_matches("web")
    assert "Company Website" in source_matches("site")
    assert "Welcome to the Jungle" in source_matches("wttj")


def test_real_jam_notes_backfill_applicant_count() -> None:
    assert infer_applicant_count("46 people clicked apply") == 46
    assert infer_applicant_count("38 people clicked apply") == 38
    assert infer_applicant_count("90 applicants") == 90
    assert infer_applicant_count("23 people applied") == 23


def test_applicant_count_validation() -> None:
    assert normalize_applicant_count("0") == 0
    assert normalize_applicant_count("123") == 123
    assert normalize_applicant_count(45) == 45

    for invalid in ("12 people", "1.5", "-1", "abc"):
        try:
            normalize_applicant_count(invalid)
        except ValueError:
            pass
        else:
            raise AssertionError(f"Expected ValueError for {invalid!r}")


def test_applicant_meter_thresholds() -> None:
    assert applicant_competition_color(0) == "#047857"
    assert applicant_competition_color(30) == "#34D399"
    assert applicant_competition_color(50) == "#EAB308"
    assert applicant_competition_color(70) == "#F97316"
    assert applicant_competition_color(100) == "#B91C1C"


def test_linkedin_location_normalization() -> None:
    result = normalize_location("Paris, Île-de-France, France")
    assert result["display"] == "Paris, France"
    assert result["city"] == "Paris"
    assert result["country"] == "France"
    assert result["lat"] is not None
    assert result["lon"] is not None


def test_common_real_jam_location_variants() -> None:
    assert normalize_location("FRA-Paris La Défense")["display"] == "Paris, France"
    assert normalize_location("Paris La Défense")["display"] == "Paris, France"
    assert normalize_location("Paris, FR")["display"] == "Paris, France"
    assert normalize_location("Neuilly-sur-Seine, Île-de-France, France")["display"] == "Neuilly-sur-Seine, France"
    assert normalize_location("Frankfurt, Hessen, Germany")["display"] == "Frankfurt, Germany"
    assert normalize_location("Tunis, Tunisia")["display"] == "Tunis, Tunisia"


def test_multicity_and_multiline_location_normalization() -> None:
    assert normalize_location("Paris, Toulouse")["display"] == "Paris / Toulouse, France"
    saf = normalize_location(
        "2, chemin de Viercy 77950\nMontereau-sur-le-jard\nIle de France France"
    )
    assert saf["display"] == "Montereau-sur-le-Jard, France"


def test_database_migration_backfills_real_notes_and_keeps_original_text(tmp_path) -> None:
    import sqlite3
    import database

    db_path = tmp_path / "jam-v5.db"
    with sqlite3.connect(db_path) as conn:
        conn.executescript(
            """
            CREATE TABLE applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company TEXT NOT NULL DEFAULT '',
                job_title TEXT NOT NULL DEFAULT '',
                description TEXT NOT NULL DEFAULT '',
                url TEXT NOT NULL DEFAULT '',
                location TEXT NOT NULL DEFAULT '',
                work_mode TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'Saved',
                rating INTEGER NOT NULL DEFAULT 0,
                notes TEXT NOT NULL DEFAULT '',
                contact_name TEXT NOT NULL DEFAULT '',
                contact_url TEXT NOT NULL DEFAULT '',
                source TEXT NOT NULL DEFAULT '',
                salary_text TEXT NOT NULL DEFAULT '',
                date_saved TEXT NOT NULL,
                date_applied TEXT,
                updated_at TEXT NOT NULL,
                match_score INTEGER,
                analysis_json TEXT NOT NULL DEFAULT ''
            );
            """
        )
        conn.execute(
            "INSERT INTO applications(company, job_title, location, notes, date_saved, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                "Alma",
                "Data Analyst",
                "Paris, Île-de-France, France",
                "46 people clicked apply",
                "2026-10-14T10:00:00+02:00",
                "2026-10-14T10:00:00+02:00",
            ),
        )

    previous = database.DB_PATH
    database.DB_PATH = db_path
    try:
        database.init_database()
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM applications WHERE id = 1").fetchone()
            assert row is not None
            assert row["location"] == "Paris, France"
            assert row["location_raw"] == "Paris, Île-de-France, France"
            assert row["location_city"] == "Paris"
            assert row["location_country"] == "France"
            assert row["applicant_count"] == 46
            assert row["notes"] == "46 people clicked apply"
    finally:
        database.DB_PATH = previous
