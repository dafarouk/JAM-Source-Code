from __future__ import annotations

import importlib.metadata
import os
import sqlite3
import sys
from pathlib import Path

from config import (
    APP_DATA_DIR,
    BACKUP_DIR,
    DB_PATH,
    EXPORT_DIR,
    FLAGS_DIR,
    LOG_DIR,
    LOG_PATH,
    PROJECTS_DIR,
    RECOVERY_DIR,
)


class DiagnosticsService:
    PACKAGES = (
        "pywebview",
        "PyMuPDF",
        "python-docx",
        "openpyxl",
        "reportlab",
        "Pillow",
    )

    @staticmethod
    def _writable(path: Path) -> bool:
        try:
            path.mkdir(parents=True, exist_ok=True)
            probe = path / ".jam_write_test"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink(missing_ok=True)
            return True
        except Exception:
            return False

    @staticmethod
    def _check_webview2() -> dict:
        if sys.platform != "win32":
            return {
                "id": "webview2",
                "label": "Microsoft Edge WebView2 Runtime",
                "status": "info",
                "detail": "Windows-only check. It will be verified on the Windows PC running JAM.",
            }

        try:
            import winreg

            roots = (
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\EdgeUpdate\Clients"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients"),
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\EdgeUpdate\Clients"),
            )

            for hive, base_path in roots:
                try:
                    with winreg.OpenKey(hive, base_path) as base:
                        index = 0
                        while True:
                            try:
                                child_name = winreg.EnumKey(base, index)
                                index += 1
                            except OSError:
                                break

                            try:
                                with winreg.OpenKey(base, child_name) as child:
                                    values = {}
                                    value_index = 0
                                    while True:
                                        try:
                                            name, value, _kind = winreg.EnumValue(child, value_index)
                                            value_index += 1
                                            values[str(name).lower()] = value
                                        except OSError:
                                            break

                                    product_name = str(
                                        values.get("name")
                                        or values.get("productname")
                                        or ""
                                    )
                                    version = str(values.get("pv") or "")

                                    if "webview2" in product_name.lower():
                                        return {
                                            "id": "webview2",
                                            "label": "Microsoft Edge WebView2 Runtime",
                                            "status": "ok",
                                            "detail": (
                                                f"Detected version {version}."
                                                if version
                                                else "Runtime detected in the Windows registry."
                                            ),
                                        }
                            except OSError:
                                continue
                except OSError:
                    continue
        except Exception:
            pass

        # If JAM itself is already rendering through pywebview, a registry
        # miss is not proof that WebView2 is absent. Keep this as a warning.
        return {
            "id": "webview2",
            "label": "Microsoft Edge WebView2 Runtime",
            "status": "warning",
            "detail": "Runtime version could not be read from the Windows registry. If JAM is open, WebView2 is already usable.",
        }

    def run(self, cv_path: str = "") -> dict:
        checks: list[dict] = []

        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.execute("SELECT 1")
                tables = {
                    row[0]
                    for row in conn.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    ).fetchall()
                }
            required = {"applications", "settings", "application_status_history"}
            missing = sorted(required - tables)
            if missing:
                checks.append({
                    "id": "database",
                    "label": "Local database",
                    "status": "error",
                    "detail": "Missing tables: " + ", ".join(missing),
                })
            else:
                checks.append({
                    "id": "database",
                    "label": "Local database",
                    "status": "ok",
                    "detail": f"Database is readable: {DB_PATH}",
                })
        except Exception as exc:
            checks.append({
                "id": "database",
                "label": "Local database",
                "status": "error",
                "detail": str(exc),
            })

        for check_id, label, path in (
            ("app_data", "JAM data folder", APP_DATA_DIR),
            ("exports", "Exports folder", EXPORT_DIR),
            ("backups", "Backups folder", BACKUP_DIR),
            ("projects", "Projects folder", PROJECTS_DIR),
            ("logs", "Logs folder", LOG_DIR),
            ("recovery", "Recovery folder", RECOVERY_DIR),
        ):
            writable = self._writable(path)
            checks.append({
                "id": check_id,
                "label": label,
                "status": "ok" if writable else "error",
                "detail": f"{'Writable' if writable else 'Not writable'}: {path}",
            })

        flag_count = len(list(FLAGS_DIR.glob("*.png"))) if FLAGS_DIR.exists() else 0
        checks.append({
            "id": "flags",
            "label": "Offline currency flags",
            "status": "ok" if flag_count >= 20 else "warning",
            "detail": f"{flag_count} local flag asset(s) detected in {FLAGS_DIR}.",
        })

        if cv_path:
            candidate = Path(cv_path)
            if candidate.exists() and candidate.is_file():
                checks.append({
                    "id": "cv",
                    "label": "Selected CV",
                    "status": "ok",
                    "detail": f"CV file is accessible: {candidate.name}",
                })
            else:
                checks.append({
                    "id": "cv",
                    "label": "Selected CV",
                    "status": "warning",
                    "detail": "The saved CV path no longer exists.",
                })
        else:
            checks.append({
                "id": "cv",
                "label": "Selected CV",
                "status": "info",
                "detail": "No CV selected. Tracking still works; analysis requires a CV.",
            })

        checks.append(self._check_webview2())

        versions = {}
        for package in self.PACKAGES:
            try:
                versions[package] = importlib.metadata.version(package)
            except importlib.metadata.PackageNotFoundError:
                versions[package] = "not installed"

        checks.append({
            "id": "python",
            "label": "Python runtime",
            "status": "ok",
            "detail": sys.version.split()[0],
        })

        error_count = sum(1 for check in checks if check["status"] == "error")
        warning_count = sum(1 for check in checks if check["status"] == "warning")

        return {
            "healthy": error_count == 0,
            "error_count": error_count,
            "warning_count": warning_count,
            "checks": checks,
            "packages": versions,
            "log_path": str(LOG_PATH),
        }
