from __future__ import annotations

from pathlib import Path

import pytest

import backup_service
import database
from backup_service import BackupService
from repositories.application_repository import ApplicationRepository
from services.project_service import ProjectService
from services.recovery_service import RecoveryService
from services.url_utils import normalize_job_url
import services.project_service as project_service_module
import services.recovery_service as recovery_service_module


@pytest.fixture()
def isolated_jam(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_path = tmp_path / "database" / "jam.db"
    backup_dir = tmp_path / "backups"
    recovery_dir = tmp_path / "recovery"

    db_path.parent.mkdir(parents=True, exist_ok=True)
    backup_dir.mkdir(parents=True, exist_ok=True)
    recovery_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(database, "DB_PATH", db_path)
    monkeypatch.setattr(backup_service, "DB_PATH", db_path)
    monkeypatch.setattr(backup_service, "BACKUP_DIR", backup_dir)
    monkeypatch.setattr(recovery_service_module, "RECOVERY_DIR", recovery_dir)
    monkeypatch.setattr(project_service_module, "RECOVERY_DIR", recovery_dir)

    database.init_database()

    return {
        "db": db_path,
        "backups": backup_dir,
        "recovery": recovery_dir,
    }


def test_url_normalization_removes_tracking_noise():
    assert normalize_job_url(
        "https://www.example.com/jobs/42?utm_source=linkedin&foo=bar#section"
    ) == "https://example.com/jobs/42?foo=bar"


def test_linkedin_url_is_canonicalized():
    result = normalize_job_url(
        "https://www.linkedin.com/jobs/view/data-analyst-1234567890?trackingId=abc&refId=xyz"
    )
    assert result == "https://linkedin.com/jobs/view/1234567890"


def test_indeed_url_keeps_only_stable_job_key():
    result = normalize_job_url(
        "https://fr.indeed.com/viewjob?jk=abcdef123&utm_source=test&from=searchOnDesktopSerp"
    )
    assert result == "https://fr.indeed.com/viewjob?jk=abcdef123"


def test_repository_sets_date_applied_once(isolated_jam):
    repo = ApplicationRepository()

    app = repo.create(
        {
            "company": "Example",
            "job_title": "Data Analyst",
            "status": "Saved",
        }
    )
    assert app["date_applied"] is None

    applied = repo.update(app["id"], {"status": "Applied"})
    first_date = applied["date_applied"]
    assert first_date

    interviewing = repo.update(app["id"], {"status": "Interviewing"})
    assert interviewing["date_applied"] == first_date

    saved_again = repo.update(app["id"], {"status": "Saved"})
    assert saved_again["date_applied"] == first_date


def test_repository_normalizes_url_on_create_and_update(isolated_jam):
    repo = ApplicationRepository()

    app = repo.create(
        {
            "company": "Example",
            "job_title": "Analyst",
            "url": "https://www.linkedin.com/jobs/view/analyst-987654321?trackingId=x",
        }
    )
    assert app["url"] == "https://linkedin.com/jobs/view/987654321"

    updated = repo.update(
        app["id"],
        {
            "url": "https://example.com/job/1?utm_campaign=test&real=value"
        },
    )
    assert updated["url"] == "https://example.com/job/1?real=value"


def test_backup_restore_creates_safety_copy_and_restores_database(isolated_jam):
    repo = ApplicationRepository()
    backups = BackupService()

    original = repo.create(
        {
            "company": "Original Company",
            "job_title": "Original Role",
        }
    )
    backup_path = backups.create_backup("test")

    repo.delete(original["id"])
    repo.create(
        {
            "company": "Later Company",
            "job_title": "Later Role",
        }
    )

    result = backups.restore_backup(backup_path)
    rows = repo.list_all()

    assert len(rows) == 1
    assert rows[0]["company"] == "Original Company"
    assert Path(result["safety_backup"]).exists()
    assert Path(result["restored"]).resolve() == Path(backup_path).resolve()


def test_recovery_service_roundtrip(isolated_jam):
    recovery = RecoveryService()
    payload = {
        "company": "Recovered Corp",
        "job_title": "BI Analyst",
        "description": "Unsaved form",
    }

    recovery.save("main_job", payload)
    restored = recovery.get("main_job")

    assert restored is not None
    assert restored["payload"] == payload

    recovery.clear("main_job")
    assert recovery.get("main_job") is None


def test_project_dirty_state_and_recovery_snapshot(isolated_jam, tmp_path: Path):
    repo = ApplicationRepository()
    projects = ProjectService()

    repo.create({"company": "A", "job_title": "Analyst"})
    project_path = tmp_path / "project.jam"
    projects.save(project_path)

    assert projects.dirty is False
    assert projects.current_path.endswith("project.jam")

    repo.create({"company": "B", "job_title": "BI Analyst"})
    projects.mark_dirty()

    assert projects.dirty is True
    info = projects.recovery_info()
    assert info is not None
    assert info["application_count"] == 2

    # Simulate a new JAM process seeing the recovery file.
    new_service = ProjectService()
    recovered = new_service.restore_recovery()
    assert recovered["applications"] == 2
    assert new_service.dirty is True

    new_service.save_current()
    assert new_service.dirty is False
    assert new_service.recovery_info() is None
