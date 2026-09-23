from __future__ import annotations

import json
from pathlib import Path

import pytest
from openpyxl import Workbook

import database
import services.project_service as project_service_module
from repositories.application_repository import ApplicationRepository
from services.import_service import ExcelImportService
from services.project_service import ProjectService
from services.saved_view_service import SavedViewService


@pytest.fixture()
def batch2_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_path = tmp_path / "database" / "jam.db"
    recovery_dir = tmp_path / "recovery"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    recovery_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(database, "DB_PATH", db_path)
    monkeypatch.setattr(project_service_module, "RECOVERY_DIR", recovery_dir)
    database.init_database()
    return db_path


def test_batch2_schema_adds_structured_salary_and_saved_views(batch2_db):
    with database.connection() as conn:
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(applications)")}
        assert {"salary_min", "salary_max", "salary_currency", "salary_period", "salary_basis"}.issubset(columns)
        table = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='saved_views'").fetchone()
        assert table is not None


def test_duplicate_detection_uses_normalized_url_and_identity(batch2_db):
    repo = ApplicationRepository()
    first = repo.create({
        "company": "Example Corp",
        "job_title": "Data Analyst",
        "url": "https://www.linkedin.com/jobs/view/data-analyst-1234567890?trackingId=abc",
    })

    by_url = repo.find_duplicates({
        "company": "Other",
        "job_title": "Other",
        "url": "https://linkedin.com/jobs/view/1234567890?refId=noise",
    })
    assert by_url and by_url[0]["id"] == first["id"]

    by_identity = repo.find_duplicates({
        "company": "  EXAMPLE corp ",
        "job_title": "Data-Analyst",
        "url": "",
    })
    assert by_identity and by_identity[0]["id"] == first["id"]

    assert repo.find_duplicates({"company": "Example Corp", "job_title": "Data Analyst"}, exclude_id=first["id"]) == []


def test_bulk_status_update_tracks_timeline_and_date_applied(batch2_db):
    repo = ApplicationRepository()
    one = repo.create({"company": "A", "job_title": "Analyst", "status": "Saved"})
    two = repo.create({"company": "B", "job_title": "BI Analyst", "status": "Saved"})

    repo.bulk_update([one["id"], two["id"]], {"status": "Applied"})
    for application_id in (one["id"], two["id"]):
        app = repo.get(application_id)
        history = repo.status_history(application_id)
        assert app["status"] == "Applied"
        assert app["date_applied"]
        assert [item["status"] for item in history] == ["Saved", "Applied"]


def test_structured_salary_roundtrip(batch2_db):
    repo = ApplicationRepository()
    app = repo.create({
        "company": "Salary Corp",
        "job_title": "Analyst",
        "salary_text": "50-60k",
        "salary_min": 50000,
        "salary_max": 60000,
        "salary_currency": "eur",
        "salary_period": "Annual",
        "salary_basis": "Gross",
    })
    assert app["salary_min"] == 50000
    assert app["salary_max"] == 60000
    assert app["salary_currency"] == "EUR"
    assert app["salary_period"] == "Annual"
    assert app["salary_basis"] == "Gross"


def test_saved_views_roundtrip(batch2_db):
    service = SavedViewService()
    item = service.save("High priority", {
        "search": "data",
        "preset": "score_70",
        "tableFilters": {"status": ["Applied"]},
    })
    assert item["name"] == "High priority"
    assert service.list()[0]["state"]["preset"] == "score_70"

    service.rename(item["id"], "Data roles")
    assert service.list()[0]["name"] == "Data roles"
    assert service.delete(item["id"]) is True
    assert service.list() == []


def test_excel_preview_and_duplicate_skip(batch2_db, tmp_path: Path):
    repo = ApplicationRepository()
    repo.create({"company": "Existing", "job_title": "Data Analyst", "url": "https://example.com/job/1"})

    path = tmp_path / "import.xlsx"
    wb = Workbook()
    ws = wb.active
    ws.append(["Job Title", "Company", "Job URL", "Unknown Thing"])
    ws.append(["Data Analyst", "Existing", "https://example.com/job/1", "x"])
    ws.append(["BI Analyst", "New Corp", "https://example.com/job/2", "y"])
    wb.save(path)

    service = ExcelImportService(repo)
    preview = service.inspect_file(path)
    assert preview["total_rows"] == 2
    assert preview["duplicate_rows"] == 1
    assert "Unknown Thing" in preview["unknown_columns"]

    result = service.import_file(path)
    assert result["imported"] == 1
    assert result["duplicates_skipped"] == 1
    assert result["failed"] == 0


def test_old_project_without_salary_columns_still_loads(batch2_db, tmp_path: Path):
    path = tmp_path / "old.jam"
    payload = {
        "format": "JAM_PROJECT",
        "format_version": 1,
        "jam_version": "0.1.0",
        "saved_at": "2026-09-23T10:00:00+02:00",
        "applications": [{
            "id": 1,
            "company": "Old",
            "job_title": "Role",
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
            "date_saved": "2026-09-23T10:00:00+02:00",
            "date_applied": None,
            "updated_at": "2026-09-23T10:00:00+02:00",
            "match_score": None,
            "analysis_json": "",
        }],
        "status_history": [],
        "settings": {},
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    service = ProjectService()
    service.load(path)
    row = ApplicationRepository().get(1)
    assert row["salary_currency"] == ""
    assert row["salary_min"] is None
