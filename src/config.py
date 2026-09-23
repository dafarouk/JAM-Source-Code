from __future__ import annotations

import json
import os
from pathlib import Path
import sys

APP_NAME = "JAM"
APP_FULL_NAME = "JAM - Job Application Manager"
APP_VERSION = "1.0.0"
AUTHOR = "Farouk"
WEBSITE = "https://www.damergi.com"
PUBLIC_REPOSITORY = "https://github.com/dafarouk/JAM"
GITHUB_REPOSITORY = "dafarouk/JAM"
UPDATE_CHECK_INTERVAL_HOURS = 24
UPDATE_HASH_ASSET_NAME = "SHA256.txt"

# PyInstaller places bundled read-only resources under sys._MEIPASS.
# Development continues to use the normal repository root.
if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    RESOURCE_ROOT = Path(sys._MEIPASS)
else:
    RESOURCE_ROOT = Path(__file__).resolve().parents[1]

PROJECT_ROOT = RESOURCE_ROOT
UI_DIR = RESOURCE_ROOT / "ui"
ASSETS_DIR = RESOURCE_ROOT / "assets"
BRANDING_DIR = ASSETS_DIR / "branding"
FLAGS_DIR = ASSETS_DIR / "flags"
RUNTIME_DIR = RESOURCE_ROOT / "runtime"
SEMANTIC_MODEL_DIR = (
    RUNTIME_DIR
    / "models"
    / "paraphrase-multilingual-MiniLM-L12-v2"
)

UI_INDEX_PATH = UI_DIR / "index.html"
CAPTURE_UI_PATH = UI_DIR / "capture.html"

LOCAL_APPDATA = Path(
    os.getenv(
        "LOCALAPPDATA",
        Path.home() / "AppData" / "Local",
    )
)

# This small settings location intentionally stays fixed. JAM reads custom
# storage paths from here before the database/logger/services are imported.
DEFAULT_APP_DATA_DIR = LOCAL_APPDATA / "Farouk" / "JAM"
SETTINGS_DIR = DEFAULT_APP_DATA_DIR / "settings"
DATA_LOCATIONS_PATH = SETTINGS_DIR / "data_locations.json"

DOCUMENTS_DIR = Path.home() / "Documents"

DEFAULT_LOCATIONS = {
    "database": DEFAULT_APP_DATA_DIR / "database",
    "backups": DEFAULT_APP_DATA_DIR / "backups",
    "exports": DOCUMENTS_DIR / "JAM Exports",
    "projects": DOCUMENTS_DIR / "JAM Projects",
    "logs": DEFAULT_APP_DATA_DIR / "logs",
    "recovery": DEFAULT_APP_DATA_DIR / "recovery",
}


def _load_location_overrides() -> dict[str, str]:
    try:
        if not DATA_LOCATIONS_PATH.exists():
            return {}
        payload = json.loads(DATA_LOCATIONS_PATH.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            return {}
        return {
            str(key): str(value)
            for key, value in payload.items()
            if key in DEFAULT_LOCATIONS and str(value).strip()
        }
    except Exception:
        # A malformed preferences file must never prevent JAM from starting.
        return {}


_LOCATION_OVERRIDES = _load_location_overrides()


def _resolved_location(key: str) -> Path:
    raw = _LOCATION_OVERRIDES.get(key)
    if raw:
        try:
            return Path(raw).expanduser().resolve()
        except Exception:
            return Path(raw).expanduser()
    return DEFAULT_LOCATIONS[key]


APP_DATA_DIR = DEFAULT_APP_DATA_DIR
DATABASE_DIR = _resolved_location("database")
BACKUP_DIR = _resolved_location("backups")
EXPORT_DIR = _resolved_location("exports")
PROJECTS_DIR = _resolved_location("projects")
LOG_DIR = _resolved_location("logs")
RECOVERY_DIR = _resolved_location("recovery")

UPDATE_DIR = DEFAULT_APP_DATA_DIR / "updates"
UPDATE_DOWNLOAD_DIR = UPDATE_DIR
UPDATE_CACHE_FILE = SETTINGS_DIR / "update_check.json"
UPDATE_PENDING_FILE = SETTINGS_DIR / "pending_update.json"

DB_PATH = DATABASE_DIR / "jam.db"
LOG_PATH = LOG_DIR / "jam.log"

DEFAULT_WINDOW_WIDTH = 1360
DEFAULT_WINDOW_HEIGHT = 880
WINDOW_MIN_WIDTH = 1120
WINDOW_MIN_HEIGHT = 720

# Compact Capture Mode. Its content scrolls vertically.
CAPTURE_WINDOW_WIDTH = 345
CAPTURE_WINDOW_HEIGHT = 445
CAPTURE_WINDOW_TITLE = "JAM - Quick Capture"


def configured_data_location(key: str) -> Path:
    """Return the currently configured folder, including pending overrides."""
    if key not in DEFAULT_LOCATIONS:
        raise ValueError(f"Unknown JAM data location: {key}")
    overrides = _load_location_overrides()
    raw = overrides.get(key)
    if raw:
        try:
            return Path(raw).expanduser().resolve()
        except Exception:
            return Path(raw).expanduser()
    return DEFAULT_LOCATIONS[key]


def data_locations() -> dict[str, Path]:
    return {
        key: configured_data_location(key)
        for key in DEFAULT_LOCATIONS
    }


def data_location_defaults() -> dict[str, Path]:
    return dict(DEFAULT_LOCATIONS)


def save_data_location_override(key: str, path_value: str | Path) -> Path:
    """Persist a custom storage directory for the next JAM launch."""
    if key not in DEFAULT_LOCATIONS:
        raise ValueError(f"Unknown JAM data location: {key}")

    target = Path(path_value).expanduser()
    try:
        target = target.resolve()
    except Exception:
        pass

    target.mkdir(parents=True, exist_ok=True)
    SETTINGS_DIR.mkdir(parents=True, exist_ok=True)

    overrides = _load_location_overrides()
    overrides[key] = str(target)

    temp = DATA_LOCATIONS_PATH.with_suffix(".tmp")
    temp.write_text(
        json.dumps(overrides, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    temp.replace(DATA_LOCATIONS_PATH)
    return target


def ensure_runtime_dirs() -> None:
    for path in (
        DEFAULT_APP_DATA_DIR,
        DATABASE_DIR,
        BACKUP_DIR,
        SETTINGS_DIR,
        LOG_DIR,
        UPDATE_DIR,
        RECOVERY_DIR,
        EXPORT_DIR,
        PROJECTS_DIR,
    ):
        path.mkdir(
            parents=True,
            exist_ok=True,
        )
