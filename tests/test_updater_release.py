from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from config import (  # noqa: E402
    GITHUB_REPOSITORY,
    UPDATE_CHECK_INTERVAL_HOURS,
    UPDATE_DOWNLOAD_DIR,
    UPDATE_HASH_ASSET_NAME,
)
from updater import Updater  # noqa: E402


def test_updater_repository_is_configured() -> None:
    assert GITHUB_REPOSITORY == "dafarouk/JAM"
    assert UPDATE_CHECK_INTERVAL_HOURS == 24
    assert UPDATE_HASH_ASSET_NAME == "SHA256.txt"
    assert UPDATE_DOWNLOAD_DIR.name == "updates"


def test_version_parser_handles_release_tags() -> None:
    assert str(Updater._version("v1.0.0")) == "1.0.0"
    assert str(Updater._version("1.2.3")) == "1.2.3"
    assert Updater._version("not-a-version") is None


def test_setup_asset_prefers_exact_version_filename() -> None:
    assets = [
        {
            "name": "JAM-v1.2.3-Windows-x64.zip",
            "browser_download_url": "https://example.test/a.zip",
        },
        {
            "name": "JAM-Setup-1.2.3.exe",
            "browser_download_url": "https://example.test/setup.exe",
        },
    ]
    asset = Updater._setup_asset(assets, "1.2.3")
    assert asset is not None
    assert asset["name"] == "JAM-Setup-1.2.3.exe"


def test_release_notes_are_converted_to_checklist_items() -> None:
    notes = """
    ## JAM 1.0.1
    - Fixed Capture startup
    * Added Calendar reminders
    1. Improved Analyzer evidence
    """
    assert Updater._release_note_items(notes) == [
        "Fixed Capture startup",
        "Added Calendar reminders",
        "Improved Analyzer evidence",
    ]


def test_frontend_loads_updater_after_tutorial() -> None:
    index = (ROOT / "ui" / "index.html").read_text(encoding="utf-8")
    assert 'js/tutorial.js' in index
    assert 'js/updater_ui.js' in index
    assert index.index('js/updater_ui.js') > index.index('js/tutorial.js')


def test_bridge_exposes_update_actions() -> None:
    bridge = (ROOT / "src" / "bridge.py").read_text(encoding="utf-8")
    assert "def check_for_updates(" in bridge
    assert "def start_update_download(" in bridge
    assert "def get_update_progress(" in bridge
    assert "def install_update(" in bridge
    assert "def acknowledge_update_complete(" in bridge


def test_guide_documents_updates() -> None:
    guide = (ROOT / "ui" / "js" / "guide.js").read_text(encoding="utf-8")
    assert "Updates and GitHub Releases" in guide
    assert "Mises à jour et GitHub Releases" in guide
