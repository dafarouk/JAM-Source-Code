from __future__ import annotations

import ctypes
from ctypes import wintypes
from datetime import datetime
import os
import shutil
import sqlite3
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path

import webview

from app_logger import logger
from backup_service import BackupService
from config import (
    APP_DATA_DIR,
    APP_FULL_NAME,
    APP_VERSION,
    AUTHOR,
    BACKUP_DIR,
    DB_PATH,
    EXPORT_DIR,
    FLAGS_DIR,
    LOG_DIR,
    LOG_PATH,
    PROJECT_ROOT,
    PROJECTS_DIR,
    RECOVERY_DIR,
    PUBLIC_REPOSITORY,
    WEBSITE,
    save_data_location_override,
    configured_data_location,
)
from database import reset_database_data
from repositories.application_repository import ApplicationRepository
from services.analysis_history_service import AnalysisHistoryService
from services.analyzer_report_service import AnalyzerReportService
from services.cv_preview_service import CVPreviewService
from services.export_service import ExportService
from services.import_service import ExcelImportService
from services.diagnostics_service import DiagnosticsService
from services.recovery_service import RecoveryService
from services.project_service import ProjectService
from services.settings_service import SettingsService
from services.saved_view_service import SavedViewService
from services.application_tracking_service import ApplicationTrackingService
from services.calendar_service import CalendarService
from updater import Updater


class JamApi:
    def __init__(self, startup_project: str | None = None) -> None:
        # Keep backend objects private. pywebview exposes public attributes
        # recursively through js_api, so native/service objects stay private.
        self._main_window = None
        self._startup_project = str(startup_project or "").strip()

        # Capture Mode is deliberately NOT another pywebview window.
        # It runs as its own lightweight Tk process so the main WebView is
        # never resized, pinned, moved or corrupted.
        self._capture_process = None
        self._capture_waiter = None
        self._shutting_down = False

        self._repo = ApplicationRepository()
        self._settings = SettingsService()
        self._saved_views = SavedViewService()
        self._tracking = ApplicationTrackingService()
        self._calendar = CalendarService()
        # Analyzer is intentionally lazy-loaded. Importing the multilingual
        # stack (sentence-transformers / PyTorch) during JAM startup makes the
        # whole application pay the Analyzer cost even when it is never used.
        self._analyzer = None
        self._analyzer_lock = threading.Lock()
        self._analysis_history = AnalysisHistoryService()
        self._analysis_reports = AnalyzerReportService()
        self._cv_preview = CVPreviewService()
        self._exports = ExportService()
        self._imports = ExcelImportService(self._repo)
        self._diagnostics = DiagnosticsService()
        self._recovery = RecoveryService()
        self._projects = ProjectService()
        self._backups = BackupService()
        self._updater = Updater()

    # --------------------------------------------------------
    # INTERNAL WINDOW MANAGEMENT
    # --------------------------------------------------------

    def _set_main_window(self, window) -> None:
        self._main_window = window

    def _get_analyzer(self):
        """Create the heavy Analyzer only when the user actually requests it."""
        if self._analyzer is not None:
            return self._analyzer

        with self._analyzer_lock:
            if self._analyzer is None:
                from services.analyzer_service import AnalyzerService

                self._analyzer = AnalyzerService()

        return self._analyzer

    def _require_main_window(self):
        if self._main_window is None:
            raise RuntimeError("JAM main window is not ready.")
        return self._main_window

    def _dialog_window(self):
        return (
            webview.active_window()
            or self._main_window
        )

    def _main_monitor_work_area(self) -> tuple[int, int, int, int]:
        """
        Return the native Windows work area of the monitor containing the
        main JAM window. Values are physical desktop coordinates.
        """
        if os.name != "nt":
            return (0, 0, 1920, 1080)

        try:
            user32 = ctypes.windll.user32
            user32.FindWindowW.restype = wintypes.HWND

            hwnd = user32.FindWindowW(
                None,
                APP_FULL_NAME,
            )

            MONITOR_DEFAULTTONEAREST = 2

            class RECT(ctypes.Structure):
                _fields_ = [
                    ("left", ctypes.c_long),
                    ("top", ctypes.c_long),
                    ("right", ctypes.c_long),
                    ("bottom", ctypes.c_long),
                ]

            class MONITORINFO(ctypes.Structure):
                _fields_ = [
                    ("cbSize", wintypes.DWORD),
                    ("rcMonitor", RECT),
                    ("rcWork", RECT),
                    ("dwFlags", wintypes.DWORD),
                ]

            if hwnd:
                monitor = user32.MonitorFromWindow(
                    hwnd,
                    MONITOR_DEFAULTTONEAREST,
                )
            else:
                monitor = user32.MonitorFromPoint(
                    wintypes.POINT(0, 0),
                    MONITOR_DEFAULTTONEAREST,
                )

            info = MONITORINFO()
            info.cbSize = ctypes.sizeof(MONITORINFO)

            if not user32.GetMonitorInfoW(
                monitor,
                ctypes.byref(info),
            ):
                raise RuntimeError("GetMonitorInfoW failed.")

            return (
                int(info.rcWork.left),
                int(info.rcWork.top),
                int(info.rcWork.right),
                int(info.rcWork.bottom),
            )

        except Exception:
            logger.exception(
                "Could not determine JAM monitor work area."
            )
            return (0, 0, 1920, 1080)

    def _restore_main_after_capture(self) -> None:
        if self._shutting_down:
            return

        main = self._main_window
        if main is None:
            return

        try:
            capture_changed = RECOVERY_DIR / "capture_changed.flag"
            if capture_changed.exists():
                self._mark_project_dirty()
                try:
                    capture_changed.unlink()
                except Exception:
                    pass

            # The main window was only minimized. It was never resized,
            # moved or set to always-on-top.
            main.show()
            main.restore()
            main.maximize()

            try:
                main.run_js(
                    "window.jamRefreshFromCapture && "
                    "window.jamRefreshFromCapture();"
                )
            except Exception:
                pass

        except Exception:
            logger.exception(
                "Could not restore JAM after Capture Mode."
            )

    def _wait_for_capture_process(
        self,
        process,
    ) -> None:
        try:
            process.wait()
        except Exception:
            logger.exception(
                "Capture Mode process wait failed."
            )
        finally:
            if self._capture_process is process:
                self._capture_process = None

            if not self._shutting_down:
                self._restore_main_after_capture()

    def _close_capture_for_shutdown(self) -> None:
        """
        Called when the real JAM application is closing.

        Stop the separate Capture process without restoring the main window.
        """
        self._shutting_down = True

        process = self._capture_process
        self._capture_process = None

        if process is None:
            return

        try:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=1.5)
                except Exception:
                    process.kill()
        except Exception:
            pass

    def _mark_project_dirty(self) -> None:
        try:
            self._projects.mark_dirty()
        except Exception:
            logger.exception("Could not update .jam dirty state.")

    def _require_no_dirty_project(self, force: bool = False) -> None:
        if self._projects.dirty and not force:
            raise RuntimeError(
                "Unsaved .jam project changes exist. Save or discard them before continuing."
            )

    def handle_close_request(self) -> bool:
        """Return True when JAM may close, False when closing is cancelled."""
        try:
            if not self._projects.dirty:
                return True

            if os.name != "nt":
                # On non-Windows test/dev environments, do not block shutdown.
                return True

            user32 = ctypes.windll.user32
            MB_YESNOCANCEL = 0x00000003
            MB_ICONWARNING = 0x00000030
            IDYES = 6
            IDNO = 7
            IDCANCEL = 2

            language = self._settings.get("language", "en").strip().lower()

            if language == "fr":
                message = (
                    "Ce projet .jam contient des modifications non enregistrées.\n\n"
                    "Oui = enregistrer les modifications et fermer\n"
                    "Non = fermer sans mettre à jour le fichier .jam\n"
                    "Annuler = revenir à JAM"
                )
                title = "JAM - Modifications non enregistrées"
            else:
                message = (
                    "This .jam project has unsaved changes.\n\n"
                    "Yes = save changes and close\n"
                    "No = close without updating the .jam file\n"
                    "Cancel = return to JAM"
                )
                title = "JAM - Unsaved project changes"

            result = user32.MessageBoxW(
                None,
                message,
                title,
                MB_YESNOCANCEL | MB_ICONWARNING,
            )

            if result == IDCANCEL:
                return False

            if result == IDYES:
                self._projects.save_current()
                logger.info("Saved active JAM project before closing.")
                return True

            if result == IDNO:
                self._projects.discard_dirty_state()
                logger.warning("Closed JAM without saving active .jam project changes.")
                return True

            return False

        except Exception:
            logger.exception("Could not process JAM close request.")
            return False

    # --------------------------------------------------------
    # COMMON RESPONSE HELPERS
    # --------------------------------------------------------

    def _ok(self, **payload) -> dict:
        return {
            "ok": True,
            **payload,
        }

    def _error(self, exc: Exception) -> dict:
        logger.exception(
            "API error: %s",
            exc,
        )
        return {
            "ok": False,
            "error": str(exc),
        }

    # --------------------------------------------------------
    # BOOTSTRAP / APPLICATIONS
    # --------------------------------------------------------

    def bootstrap(self) -> dict:
        try:
            startup_project = None
            startup_error = ""

            if self._startup_project:
                requested = self._startup_project
                self._startup_project = ""
                try:
                    startup_project = self._projects.load(requested)
                    logger.info("JAM project opened from Windows shell: %s", requested)
                except Exception as exc:
                    startup_error = str(exc)
                    logger.exception("Could not open startup JAM project: %s", requested)

            return self._ok(
                version=APP_VERSION,
                startup_project=startup_project,
                startup_project_error=startup_error,
                applications=self._repo.list_all(),
                stats=self._repo.stats(),
                recent_projects=self._projects.recent(),
                export_history=self._exports.history(),
                saved_views=self._saved_views.list(),
                analysis_history=self._analysis_history.list(),
                calendar_events=self._calendar.list_all(),
                settings=self._settings.all(),
                backup_dir=str(BACKUP_DIR),
                backups=self._backups.list_backups(),
                project_state=self._projects.state(),
                data_locations={
                    "database": str(configured_data_location("database")),
                    "database_file": str(DB_PATH),
                    "app_data": str(APP_DATA_DIR),
                    "backups": str(configured_data_location("backups")),
                    "exports": str(configured_data_location("exports")),
                    "projects": str(configured_data_location("projects")),
                    "logs": str(configured_data_location("logs")),
                    "log_file": str(LOG_PATH),
                    "recovery": str(configured_data_location("recovery")),
                    "flags": str(FLAGS_DIR),
                },
                updater=self._updater.status(),
            )
        except Exception as exc:
            return self._error(exc)

    # --------------------------------------------------------
    # UPDATER / GITHUB RELEASES
    # --------------------------------------------------------

    def get_update_status(self) -> dict:
        try:
            return self._ok(
                updater=self._updater.status(),
            )
        except Exception as exc:
            return self._error(exc)

    def check_for_updates(self, manual: bool = False) -> dict:
        try:
            return self._ok(
                update=self._updater.check(bool(manual)),
            )
        except Exception as exc:
            return self._error(exc)

    def start_update_download(self) -> dict:
        try:
            return self._ok(
                update=self._updater.start_download(),
            )
        except Exception as exc:
            return self._error(exc)

    def get_update_progress(self) -> dict:
        try:
            return self._ok(
                progress=self._updater.progress(),
            )
        except Exception as exc:
            return self._error(exc)

    def install_update(self) -> dict:
        try:
            # Updating closes JAM. Protect an active dirty .jam project first.
            if not self.handle_close_request():
                return self._ok(
                    update={
                        "ok": False,
                        "message": "Update installation was cancelled to protect unsaved project changes.",
                    }
                )

            result = self._updater.install_downloaded()
            if not result.get("ok"):
                return self._ok(update=result)

            def close_for_update() -> None:
                # Give the frontend a moment to show the final updater message
                # before JAM releases its installed files to Inno Setup.
                time.sleep(1.4)
                self._shutting_down = True
                try:
                    self._close_capture_for_shutdown()
                except Exception:
                    pass

                try:
                    if self._main_window is not None:
                        self._main_window.destroy()
                except Exception:
                    logger.exception("Could not close JAM for update installation.")

            threading.Thread(
                target=close_for_update,
                daemon=True,
                name="jam-update-shutdown",
            ).start()

            return self._ok(update=result)

        except Exception as exc:
            return self._error(exc)

    def acknowledge_update_complete(self) -> dict:
        try:
            self._updater.acknowledge_completed_update()
            return self._ok()
        except Exception as exc:
            return self._error(exc)

    def save_application(self, payload: dict) -> dict:
        try:
            app_id = payload.get("id")

            if app_id:
                application = self._repo.update(
                    int(app_id),
                    payload,
                )
                logger.info(
                    "Updated application %s",
                    app_id,
                )
            else:
                application = self._repo.create(
                    payload
                )
                logger.info(
                    "Created application %s | %s | %s",
                    application.get("id"),
                    application.get("company"),
                    application.get("job_title"),
                )

            self._recovery.clear("main_job")
            self._mark_project_dirty()

            return self._ok(
                application=application,
                stats=self._repo.stats(),
                project_state=self._projects.state(),
            )

        except Exception as exc:
            return self._error(exc)

    def delete_application(
        self,
        application_id: int,
    ) -> dict:
        try:
            self._repo.delete(
                int(application_id)
            )

            logger.info(
                "Deleted application %s",
                application_id,
            )

            self._mark_project_dirty()

            return self._ok(
                stats=self._repo.stats(),
                project_state=self._projects.state(),
            )

        except Exception as exc:
            return self._error(exc)

    def delete_applications(
        self,
        application_ids: list[int],
    ) -> dict:
        try:
            count = self._repo.delete_many(
                application_ids
            )

            logger.info(
                "Deleted %s applications",
                count,
            )

            if count:
                self._mark_project_dirty()

            return self._ok(
                deleted=count,
                stats=self._repo.stats(),
                project_state=self._projects.state(),
            )

        except Exception as exc:
            return self._error(exc)

    def get_application_details(self, application_id: int) -> dict:
        try:
            application = self._repo.details(int(application_id))
            if not application:
                raise ValueError("Application not found.")
            return self._ok(application=application)
        except Exception as exc:
            return self._error(exc)

    def check_duplicates(self, payload: dict) -> dict:
        try:
            exclude_id = payload.get("id")
            matches = self._repo.find_duplicates(
                payload,
                int(exclude_id) if exclude_id else None,
            )
            return self._ok(duplicates=matches)
        except Exception as exc:
            return self._error(exc)

    def bulk_update_applications(self, application_ids: list[int], payload: dict) -> dict:
        try:
            rows = self._repo.bulk_update(application_ids, payload or {})
            if rows:
                self._mark_project_dirty()
            logger.info("Bulk updated %s applications | fields=%s", len(rows), sorted((payload or {}).keys()))
            return self._ok(
                updated=len(rows),
                applications=self._repo.list_all(),
                stats=self._repo.stats(),
                project_state=self._projects.state(),
            )
        except Exception as exc:
            return self._error(exc)

    # --------------------------------------------------------
    # BATCH 3 — APPLICATION TRACKING
    # --------------------------------------------------------

    def get_application_tracking(self, application_id: int) -> dict:
        try:
            return self._ok(
                tracking=self._tracking.details(int(application_id))
            )
        except Exception as exc:
            return self._error(exc)

    def add_application_contact(self, application_id: int, payload: dict) -> dict:
        try:
            item = self._tracking.add_contact(int(application_id), payload or {})
            self._mark_project_dirty()
            return self._ok(item=item, tracking=self._tracking.details(int(application_id)))
        except Exception as exc:
            return self._error(exc)

    def update_application_contact(self, contact_id: int, payload: dict) -> dict:
        try:
            item = self._tracking.update_contact(int(contact_id), payload or {})
            app_id = int(item["application_id"])
            self._mark_project_dirty()
            return self._ok(item=item, tracking=self._tracking.details(app_id))
        except Exception as exc:
            return self._error(exc)

    def delete_application_contact(self, application_id: int, contact_id: int) -> dict:
        try:
            deleted = self._tracking.delete_contact(int(contact_id))
            if deleted:
                self._mark_project_dirty()
            return self._ok(
                deleted=deleted,
                tracking=self._tracking.details(int(application_id)),
            )
        except Exception as exc:
            return self._error(exc)

    def add_application_note(self, application_id: int, text: str) -> dict:
        try:
            item = self._tracking.add_note(int(application_id), text)
            self._mark_project_dirty()
            return self._ok(item=item, tracking=self._tracking.details(int(application_id)))
        except Exception as exc:
            return self._error(exc)

    def update_application_note(self, application_id: int, note_id: int, text: str) -> dict:
        try:
            item = self._tracking.update_note(int(note_id), text)
            self._mark_project_dirty()
            return self._ok(item=item, tracking=self._tracking.details(int(application_id)))
        except Exception as exc:
            return self._error(exc)

    def delete_application_note(self, application_id: int, note_id: int) -> dict:
        try:
            deleted = self._tracking.delete_note(int(note_id))
            if deleted:
                self._mark_project_dirty()
            return self._ok(
                deleted=deleted,
                tracking=self._tracking.details(int(application_id)),
            )
        except Exception as exc:
            return self._error(exc)

    def _choose_attachment_file_native(self) -> str | None:
        if os.name != "nt":
            main = self._require_main_window()
            result = main.create_file_dialog(
                webview.FileDialog.OPEN,
                allow_multiple=False,
                file_types=("All files (*.*)",),
            )
            if not result:
                return None
            return str(result[0] if isinstance(result, (list, tuple)) else result)

        script = r"""
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
Add-Type -AssemblyName System.Windows.Forms
$dialog = New-Object System.Windows.Forms.OpenFileDialog
$dialog.Title = 'Attach file to application'
$dialog.Filter = 'Documents and images|*.pdf;*.doc;*.docx;*.txt;*.png;*.jpg;*.jpeg;*.webp;*.xlsx;*.xlsm|All files|*.*'
$dialog.Multiselect = $false
$dialog.CheckFileExists = $true
$dialog.CheckPathExists = $true
$dialog.RestoreDirectory = $true
$result = $dialog.ShowDialog()
if ($result -eq [System.Windows.Forms.DialogResult]::OK) {
    [Console]::Write($dialog.FileName)
}
$dialog.Dispose()
"""
        completed = subprocess.run(
            ["powershell.exe", "-NoProfile", "-STA", "-NonInteractive", "-Command", script],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(completed.stderr.strip() or "Attachment file picker failed.")
        selected = completed.stdout.strip()
        return selected or None

    def add_application_attachment(self, application_id: int, category: str = "Other") -> dict:
        try:
            path = self._choose_attachment_file_native()
            if not path:
                return self._ok(cancelled=True)
            item = self._tracking.add_attachment(int(application_id), path, category)
            self._mark_project_dirty()
            return self._ok(item=item, tracking=self._tracking.details(int(application_id)))
        except Exception as exc:
            return self._error(exc)

    def delete_application_attachment(self, application_id: int, attachment_id: int) -> dict:
        try:
            deleted = self._tracking.delete_attachment(int(attachment_id))
            if deleted:
                self._mark_project_dirty()
            return self._ok(
                deleted=deleted,
                tracking=self._tracking.details(int(application_id)),
            )
        except Exception as exc:
            return self._error(exc)

    def reset_all_data(self, force: bool = False) -> dict:
        try:
            self._require_no_dirty_project(force=bool(force))
            reset_database_data()
            self._recovery.clear_all()
            self._projects.clear_active_project()
            logger.warning(
                "User reset all JAM database data."
            )
            return self._ok()

        except Exception as exc:
            return self._error(exc)

    # --------------------------------------------------------
    # CV / ANALYZER
    # --------------------------------------------------------

    def choose_cv(self) -> dict:
        try:
            window = self._dialog_window()

            if window is None:
                raise RuntimeError(
                    "JAM window is not ready."
                )

            result = window.create_file_dialog(
                webview.OPEN_DIALOG,
                allow_multiple=False,
                file_types=(
                    "CV files (*.pdf;*.docx;*.txt;*.cvm)",
                    "PDF files (*.pdf)",
                    "Word files (*.docx)",
                    "CVM project files (*.cvm)",
                    "All files (*.*)",
                ),
            )

            if not result:
                return self._ok(
                    cancelled=True
                )

            path = (
                result[0]
                if isinstance(
                    result,
                    (list, tuple),
                )
                else result
            )

            self._settings.set(
                "cv_path",
                str(path),
            )
            self._mark_project_dirty()

            logger.info(
                "CV selected: %s",
                path,
            )

            return self._ok(
                path=str(path)
            )

        except Exception as exc:
            return self._error(exc)

    def analyze_job(
        self,
        payload: dict,
    ) -> dict:
        try:
            title = str(
                payload.get("job_title")
                or ""
            ).strip()

            description = str(
                payload.get("description")
                or ""
            ).strip()

            if not title and not description:
                raise ValueError(
                    "Add a job title or description before analyzing."
                )

            analysis = self._get_analyzer().analyze(
                title,
                description,
            )

            app_id = payload.get("id")

            if app_id:
                self._repo.set_analysis(
                    int(app_id),
                    analysis.get("score"),
                    analysis,
                )

            logger.info(
                "Analyzed job | title=%s | score=%s | confidence=%s",
                title,
                analysis.get("score"),
                analysis.get("confidence"),
            )

            return self._ok(
                analysis=analysis
            )

        except Exception as exc:
            return self._error(exc)

    def export_analysis_pdf(self, payload: dict) -> dict:
        try:
            title = str(payload.get("job_title") or "").strip()
            description = str(payload.get("description") or "").strip()
            analysis = payload.get("analysis") or {}

            if not analysis:
                raise ValueError("Analyze a role before exporting the Analyzer PDF.")

            path = self._analysis_reports.export(
                title,
                description,
                analysis,
            )

            logger.info(
                "Analyzer PDF export created: %s",
                path,
            )

            return self._ok(path=path)
        except Exception as exc:
            return self._error(exc)

    def get_cv_preview(self) -> dict:
        try:
            return self._ok(
                preview=self._cv_preview.preview()
            )
        except Exception as exc:
            return self._error(exc)

    def list_analysis_history(self) -> dict:
        try:
            return self._ok(
                items=self._analysis_history.list()
            )
        except Exception as exc:
            return self._error(exc)

    def save_analysis_history(self, payload: dict) -> dict:
        try:
            item = self._analysis_history.save(
                payload.get("job_title", ""),
                payload.get("description", ""),
                payload.get("analysis") or {},
            )
            logger.info(
                "Saved analyzer history %s | title=%s | score=%s",
                item.get("id"),
                item.get("job_title"),
                item.get("score"),
            )
            return self._ok(
                item=item,
                items=self._analysis_history.list(),
            )
        except Exception as exc:
            return self._error(exc)

    def delete_analysis_history(self, history_id: int) -> dict:
        try:
            deleted = self._analysis_history.delete(int(history_id))
            return self._ok(
                deleted=deleted,
                items=self._analysis_history.list(),
            )
        except Exception as exc:
            return self._error(exc)

    def save_setting(
        self,
        key: str,
        value: str,
    ) -> dict:
        try:
            allowed = {
                "cv_path",
                "salary_target_min",
                "salary_target_max",
                "capture_corner",
                "capture_remember_geometry",
                "salary_currency",
                "language",
                "notifications_enabled",
                "notify_interview_tomorrow",
                "notify_interview_hour",
                "notify_followup_due",
                "notify_stale_application",
                "notify_deadline",
                "notify_unanalyzed",
                "notify_backup_stale",
                "notify_upcoming_week",
                "notify_inactivity",
                "tutorial_completed",
            }

            if key not in allowed:
                raise ValueError(
                    "Unsupported setting."
                )

            self._settings.set(
                key,
                value,
            )

            # Tutorial completion is a device/app preference, not project data.
            if key != "tutorial_completed":
                self._mark_project_dirty()

            return self._ok(
                project_state=self._projects.state(),
            )

        except Exception as exc:
            return self._error(exc)

    def save_notification_settings(self, payload: dict) -> dict:
        try:
            allowed = {
                "notifications_enabled",
                "notify_interview_tomorrow",
                "notify_interview_hour",
                "notify_followup_due",
                "notify_stale_application",
                "notify_deadline",
                "notify_unanalyzed",
                "notify_backup_stale",
                "notify_upcoming_week",
                "notify_inactivity",
            }

            values = payload or {}
            for key in allowed:
                raw = values.get(key, "1")
                value = "0" if str(raw).strip().lower() in {"0", "false", "off", "no"} else "1"
                self._settings.set(key, value)

            self._mark_project_dirty()
            return self._ok(
                settings=self._settings.all(),
                project_state=self._projects.state(),
            )
        except Exception as exc:
            return self._error(exc)

    # --------------------------------------------------------
    # CALENDAR / REMINDERS
    # --------------------------------------------------------

    def list_calendar_events(self) -> dict:
        try:
            return self._ok(
                events=self._calendar.list_all(),
            )
        except Exception as exc:
            return self._error(exc)

    def save_calendar_event(self, payload: dict) -> dict:
        try:
            item = self._calendar.save(payload or {})
            self._mark_project_dirty()
            return self._ok(
                item=item,
                events=self._calendar.list_all(),
                project_state=self._projects.state(),
            )
        except Exception as exc:
            return self._error(exc)

    def delete_calendar_event(self, event_id: int) -> dict:
        try:
            deleted = self._calendar.delete(int(event_id))
            if deleted:
                self._mark_project_dirty()
            return self._ok(
                deleted=deleted,
                events=self._calendar.list_all(),
                project_state=self._projects.state(),
            )
        except Exception as exc:
            return self._error(exc)

    def set_calendar_event_completed(self, event_id: int, completed: bool) -> dict:
        try:
            item = self._calendar.set_completed(
                int(event_id),
                bool(completed),
            )
            self._mark_project_dirty()
            return self._ok(
                item=item,
                events=self._calendar.list_all(),
                project_state=self._projects.state(),
            )
        except Exception as exc:
            return self._error(exc)

    # --------------------------------------------------------
    # EXPORTS
    # --------------------------------------------------------

    def export_excel(
        self,
        application_ids: list[int] | None = None,
        filter_summary: list[str] | None = None,
    ) -> dict:
        try:
            rows = self._repo.get_many(
                application_ids
            )

            if not rows:
                raise ValueError(
                    "There are no applications to export."
                )

            path = self._exports.export_excel(
                rows,
                filter_summary=filter_summary,
            )

            logger.info(
                "Excel export created: %s",
                path,
            )

            return self._ok(
                path=path,
                history=self._exports.history(),
            )

        except Exception as exc:
            return self._error(exc)

    def export_pdf(
        self,
        application_ids: list[int] | None = None,
        filter_summary: list[str] | None = None,
    ) -> dict:
        try:
            rows = self._repo.get_many(
                application_ids
            )

            if not rows:
                raise ValueError(
                    "There are no applications to export."
                )

            path = self._exports.export_pdf(
                rows,
                filter_summary=filter_summary,
            )

            logger.info(
                "PDF export created: %s",
                path,
            )

            return self._ok(
                path=path,
                history=self._exports.history(),
            )

        except Exception as exc:
            return self._error(exc)

    def _choose_excel_file_native(self) -> str | None:
        """
        Open the real Windows Excel file picker in a separate STA process.

        This avoids pywebview/Tk dialog-thread conflicts that can terminate
        JAM with:
            Tcl_AsyncDelete: async handler deleted by the wrong thread
        """
        if os.name != "nt":
            main = self._require_main_window()

            file_dialog = getattr(
                webview,
                "FileDialog",
                None,
            )

            open_mode = (
                file_dialog.OPEN
                if file_dialog is not None
                else webview.OPEN_DIALOG
            )

            result = main.create_file_dialog(
                open_mode,
                allow_multiple=False,
                file_types=(
                    "Excel files (*.xlsx;*.xlsm)",
                ),
            )

            if not result:
                return None

            return str(
                result[0]
                if isinstance(
                    result,
                    (list, tuple),
                )
                else result
            )

        script = r"""
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
Add-Type -AssemblyName System.Windows.Forms

$dialog = New-Object System.Windows.Forms.OpenFileDialog
$dialog.Title = 'Import Excel file'
$dialog.Filter = 'Excel files (*.xlsx;*.xlsm)|*.xlsx;*.xlsm'
$dialog.Multiselect = $false
$dialog.CheckFileExists = $true
$dialog.CheckPathExists = $true
$dialog.RestoreDirectory = $true

$result = $dialog.ShowDialog()

if ($result -eq [System.Windows.Forms.DialogResult]::OK) {
    [Console]::Write($dialog.FileName)
}

$dialog.Dispose()
"""

        startupinfo = None
        creationflags = 0

        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 0

            creationflags = getattr(
                subprocess,
                "CREATE_NO_WINDOW",
                0,
            )
        except Exception:
            startupinfo = None
            creationflags = 0

        completed = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-STA",
                "-NonInteractive",
                "-Command",
                script,
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            startupinfo=startupinfo,
            creationflags=creationflags,
            check=False,
        )

        if completed.returncode != 0:
            raise RuntimeError(
                completed.stderr.strip()
                or "Windows Excel file picker failed."
            )

        selected = completed.stdout.strip()

        if not selected:
            return None

        path = Path(
            selected
        ).expanduser()

        if path.suffix.lower() not in {
            ".xlsx",
            ".xlsm",
        }:
            raise ValueError(
                "Please choose an Excel .xlsx or .xlsm file."
            )

        if not path.is_file():
            raise FileNotFoundError(
                f"Excel file not found: {path}"
            )

        return str(path)

    def preview_excel_dialog(self) -> dict:
        try:
            path = self._choose_excel_file_native()

            if not path:
                return self._ok(
                    cancelled=True
                )

            preview = self._imports.inspect_file(
                path
            )

            return self._ok(
                preview=preview
            )

        except Exception as exc:
            return self._error(exc)

    def confirm_excel_import(self, path: str, import_duplicates: bool = False) -> dict:
        try:
            summary = self._imports.import_file(
                str(path),
                import_duplicates=bool(import_duplicates),
            )
            logger.info(
                "Excel import completed | imported=%s | skipped=%s | duplicates=%s | failed=%s | file=%s",
                summary.get("imported", 0),
                summary.get("skipped", 0),
                summary.get("duplicates_skipped", 0),
                summary.get("failed", 0),
                path,
            )
            if summary.get("imported"):
                self._mark_project_dirty()
            return self._ok(
                summary=summary,
                applications=self._repo.list_all(),
                stats=self._repo.stats(),
                project_state=self._projects.state(),
            )
        except Exception as exc:
            return self._error(exc)

    def import_excel_dialog(self) -> dict:
        try:
            path = self._choose_excel_file_native()

            if not path:
                return self._ok(
                    cancelled=True
                )

            summary = self._imports.import_file(
                path
            )

            logger.info(
                "Excel import completed | imported=%s | skipped=%s | file=%s",
                summary["imported"],
                summary["skipped"],
                path,
            )

            if summary.get("imported"):
                self._mark_project_dirty()

            return self._ok(
                summary=summary,
                applications=self._repo.list_all(),
                stats=self._repo.stats(),
            )

        except Exception as exc:
            return self._error(exc)

    # --------------------------------------------------------
    # .JAM PROJECTS
    # --------------------------------------------------------

    def save_project(self) -> dict:
        try:
            main = self._require_main_window()

            suggested_name = (
                f"JAM_{datetime.now().strftime('%d%m%Y_%H%M')}.jam"
            )

            result = main.create_file_dialog(
                webview.FileDialog.SAVE,
                directory=str(PROJECTS_DIR),
                save_filename=suggested_name,
                file_types=(
                    "JAM Project (*.jam)",
                ),
            )

            if not result:
                return self._ok(
                    cancelled=True
                )

            path = (
                result[0]
                if isinstance(
                    result,
                    (list, tuple),
                )
                else result
            )

            saved = self._projects.save(
                str(path)
            )

            logger.info(
                "JAM project saved: %s",
                saved,
            )

            return self._ok(
                path=saved,
                recent_projects=self._projects.recent(),
                project_state=self._projects.state(),
            )

        except Exception as exc:
            return self._error(exc)

    def open_project_dialog(self, force: bool = False) -> dict:
        try:
            self._require_no_dirty_project(force=bool(force))
            main = self._require_main_window()

            result = main.create_file_dialog(
                webview.OPEN_DIALOG,
                allow_multiple=False,
                directory=str(PROJECTS_DIR),
                file_types=(
                    "JAM Project (*.jam)",
                ),
            )

            if not result:
                return self._ok(
                    cancelled=True
                )

            path = (
                result[0]
                if isinstance(
                    result,
                    (list, tuple),
                )
                else result
            )

            loaded = self._projects.load(
                str(path)
            )

            logger.info(
                "JAM project opened: %s",
                path,
            )

            return self._ok(
                project=loaded,
                applications=self._repo.list_all(),
                stats=self._repo.stats(),
                recent_projects=self._projects.recent(),
                project_state=self._projects.state(),
            )

        except Exception as exc:
            return self._error(exc)

    def open_recent_project(
        self,
        path: str,
        force: bool = False,
    ) -> dict:
        try:
            self._require_no_dirty_project(force=bool(force))
            loaded = self._projects.load(
                path
            )

            logger.info(
                "Recent JAM project opened: %s",
                path,
            )

            return self._ok(
                project=loaded,
                applications=self._repo.list_all(),
                stats=self._repo.stats(),
                recent_projects=self._projects.recent(),
                project_state=self._projects.state(),
            )

        except Exception as exc:
            return self._error(exc)

    def remove_recent_project(self, path: str) -> dict:
        try:
            removed = self._projects.remove_recent(path)
            return self._ok(removed=removed, recent_projects=self._projects.recent())
        except Exception as exc:
            return self._error(exc)

    # --------------------------------------------------------
    # SAVED VIEWS / EXPORT HISTORY
    # --------------------------------------------------------

    def list_saved_views(self) -> dict:
        try:
            return self._ok(items=self._saved_views.list())
        except Exception as exc:
            return self._error(exc)

    def save_view(self, name: str, state: dict) -> dict:
        try:
            item = self._saved_views.save(name, state or {})
            self._mark_project_dirty()
            return self._ok(item=item, items=self._saved_views.list())
        except Exception as exc:
            return self._error(exc)

    def rename_saved_view(self, view_id: int, name: str) -> dict:
        try:
            self._saved_views.rename(int(view_id), name)
            self._mark_project_dirty()
            return self._ok(items=self._saved_views.list())
        except Exception as exc:
            return self._error(exc)

    def delete_saved_view(self, view_id: int) -> dict:
        try:
            removed = self._saved_views.delete(int(view_id))
            if removed:
                self._mark_project_dirty()
            return self._ok(removed=removed, items=self._saved_views.list())
        except Exception as exc:
            return self._error(exc)

    def remove_export_history(self, history_id: int) -> dict:
        try:
            removed = self._exports.remove_history(int(history_id))
            return self._ok(removed=removed, history=self._exports.history())
        except Exception as exc:
            return self._error(exc)

    # --------------------------------------------------------
    # LOGS / BACKUP / LINKS
    # --------------------------------------------------------

    def get_logs(self) -> dict:
        try:
            if not LOG_PATH.exists():
                return self._ok(text="No logs yet.", entries=[])

            lines = LOG_PATH.read_text(
                encoding="utf-8",
                errors="ignore",
            ).splitlines()[-400:]

            entries = []
            for line in lines:
                parts = line.split(" | ", 3)
                if len(parts) == 4:
                    timestamp, level, _logger_name, message = parts
                else:
                    timestamp, level, message = "", "INFO", line

                level_upper = level.upper()
                lower = message.lower()
                if level_upper in {"ERROR", "CRITICAL"} or any(
                    token in lower for token in ("traceback", "exception", "failed", "error:")
                ):
                    kind = "error"
                    symbol = "✕"
                elif level_upper == "WARNING" or "warning" in lower:
                    kind = "warning"
                    symbol = "⚠"
                elif any(
                    token in lower
                    for token in (
                        "created", "saved", "opened", "updated", "completed", "selected",
                        "deleted", "backup created", "export created", "import completed",
                    )
                ):
                    kind = "success"
                    symbol = "✓"
                else:
                    kind = "info"
                    symbol = "•"

                entries.append({
                    "timestamp": timestamp,
                    "level": level_upper,
                    "message": message,
                    "kind": kind,
                    "symbol": symbol,
                })

            return self._ok(
                text="\n".join(lines),
                entries=entries,
            )

        except Exception as exc:
            return self._error(exc)

    def create_backup(self) -> dict:
        try:
            path = self._backups.create_backup()

            logger.info(
                "Database backup created: %s",
                path,
            )

            return self._ok(
                path=path,
                backups=self._backups.list_backups(),
            )

        except Exception as exc:
            return self._error(exc)

    def list_backups(self) -> dict:
        try:
            return self._ok(
                backups=self._backups.list_backups(),
            )
        except Exception as exc:
            return self._error(exc)

    def restore_backup(self, path: str, force: bool = False) -> dict:
        try:
            self._require_no_dirty_project(force=bool(force))
            result = self._backups.restore_backup(path)
            self._projects.clear_active_project()
            self._recovery.clear_all()
            logger.warning(
                "Database backup restored: %s | safety=%s",
                result.get("restored"),
                result.get("safety_backup"),
            )
            return self._ok(
                restore=result,
                applications=self._repo.list_all(),
                stats=self._repo.stats(),
                settings=self._settings.all(),
                backups=self._backups.list_backups(),
                project_state=self._projects.state(),
            )
        except Exception as exc:
            return self._error(exc)

    def save_draft(self, name: str, payload: dict) -> dict:
        try:
            return self._ok(
                draft=self._recovery.save(name, payload),
            )
        except Exception as exc:
            return self._error(exc)

    def get_draft(self, name: str) -> dict:
        try:
            return self._ok(
                draft=self._recovery.get(name),
            )
        except Exception as exc:
            return self._error(exc)

    def clear_draft(self, name: str) -> dict:
        try:
            self._recovery.clear(name)
            return self._ok()
        except Exception as exc:
            return self._error(exc)

    def project_state(self) -> dict:
        try:
            return self._ok(
                project_state=self._projects.state(),
            )
        except Exception as exc:
            return self._error(exc)

    def save_current_project(self) -> dict:
        try:
            path = self._projects.save_current()
            logger.info("Active JAM project saved: %s", path)
            return self._ok(
                path=path,
                recent_projects=self._projects.recent(),
                project_state=self._projects.state(),
            )
        except Exception as exc:
            return self._error(exc)

    def discard_project_changes(self) -> dict:
        try:
            self._projects.discard_dirty_state()
            return self._ok(
                project_state=self._projects.state(),
            )
        except Exception as exc:
            return self._error(exc)

    def restore_project_recovery(self) -> dict:
        try:
            restored = self._projects.restore_recovery()
            logger.warning("Recovered unsaved .jam project changes.")
            return self._ok(
                recovery=restored,
                applications=self._repo.list_all(),
                stats=self._repo.stats(),
                settings=self._settings.all(),
                project_state=self._projects.state(),
            )
        except Exception as exc:
            return self._error(exc)

    def discard_project_recovery(self) -> dict:
        try:
            self._projects.discard_recovery()
            return self._ok(
                project_state=self._projects.state(),
            )
        except Exception as exc:
            return self._error(exc)

    def run_diagnostics(self) -> dict:
        try:
            result = self._diagnostics.run(
                self._settings.get("cv_path", "")
            )
            logger.info(
                "Diagnostics completed | healthy=%s | errors=%s | warnings=%s",
                result.get("healthy"),
                result.get("error_count"),
                result.get("warning_count"),
            )
            return self._ok(
                diagnostics=result,
            )
        except Exception as exc:
            return self._error(exc)

    def open_path(
        self,
        path: str,
    ) -> dict:
        try:
            candidate = Path(path)

            if not candidate.exists():
                raise FileNotFoundError(
                    "The file or folder no longer exists."
                )

            os.startfile(
                str(candidate)
            )

            return self._ok()

        except Exception as exc:
            return self._error(exc)

    def open_parent_folder(self, path: str) -> dict:
        try:
            candidate = Path(path)
            parent = candidate if candidate.is_dir() else candidate.parent
            return self.open_path(str(parent))
        except Exception as exc:
            return self._error(exc)

    def open_exports_folder(self) -> dict:
        return self.open_path(
            str(EXPORT_DIR)
        )

    def open_backup_folder(self) -> dict:
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        return self.open_path(str(BACKUP_DIR))

    def open_projects_folder(self) -> dict:
        return self.open_path(
            str(PROJECTS_DIR)
        )

    def open_data_location(self, key: str) -> dict:
        locations = {
            "database": configured_data_location("database"),
            "app_data": APP_DATA_DIR,
            "backups": configured_data_location("backups"),
            "exports": configured_data_location("exports"),
            "projects": configured_data_location("projects"),
            "logs": configured_data_location("logs"),
            "recovery": configured_data_location("recovery"),
            "flags": FLAGS_DIR,
        }
        path = locations.get(str(key))
        if path is None:
            return self._error(ValueError("Unknown JAM data location."))
        Path(path).mkdir(parents=True, exist_ok=True)
        return self.open_path(str(path))

    @staticmethod
    def _copy_location_contents(source: Path, target: Path) -> None:
        source = source.resolve()
        target = target.resolve()

        if source == target or not source.exists():
            return

        # Prevent recursive copies such as logs -> logs/new-folder.
        if source in target.parents:
            raise ValueError(
                "Choose a folder outside the current JAM storage folder."
            )

        target.mkdir(parents=True, exist_ok=True)

        for item in source.iterdir():
            destination = target / item.name
            if item.is_dir():
                shutil.copytree(
                    item,
                    destination,
                    dirs_exist_ok=True,
                )
            else:
                shutil.copy2(
                    item,
                    destination,
                )

    @staticmethod
    def _copy_database_to(target_dir: Path) -> None:
        target_dir.mkdir(parents=True, exist_ok=True)
        destination = target_dir / "jam.db"

        if not DB_PATH.exists():
            return

        if DB_PATH.resolve() == destination.resolve():
            return

        if destination.exists():
            stamp = time.strftime("%Y-%m-%d_%H-%M-%S")
            preserved = target_dir / f"jam_existing_before_move_{stamp}.db"
            shutil.copy2(destination, preserved)

        source_conn = sqlite3.connect(str(DB_PATH))
        destination_conn = sqlite3.connect(str(destination))
        try:
            source_conn.backup(destination_conn)
            destination_conn.commit()
        finally:
            destination_conn.close()
            source_conn.close()

    def edit_data_location(self, key: str) -> dict:
        """Choose a new folder for one JAM storage category.

        Existing data is copied safely. The new location becomes active after
        JAM is restarted because services import their storage paths at startup.
        """
        try:
            normalized = str(key or "").strip().lower()
            current_locations = {
                "database": DB_PATH.parent,
                "backups": BACKUP_DIR,
                "exports": EXPORT_DIR,
                "projects": PROJECTS_DIR,
                "logs": LOG_DIR,
                "recovery": RECOVERY_DIR,
            }

            current = current_locations.get(normalized)
            if current is None:
                raise ValueError("Unknown JAM data location.")

            main = self._require_main_window()
            folder_dialog = getattr(webview, "FOLDER_DIALOG", None)
            if folder_dialog is None:
                raise RuntimeError(
                    "This pywebview version does not support folder selection."
                )

            result = main.create_file_dialog(
                folder_dialog,
                directory=str(current),
            )

            if not result:
                return self._ok(cancelled=True)

            selected = (
                result[0]
                if isinstance(result, (list, tuple))
                else result
            )
            target = Path(str(selected)).expanduser()
            target.mkdir(parents=True, exist_ok=True)

            if normalized == "database":
                self._copy_database_to(target)
            else:
                self._copy_location_contents(Path(current), target)

            saved = save_data_location_override(
                normalized,
                target,
            )

            logger.info(
                "JAM data location changed | key=%s | old=%s | new=%s | restart_required=true",
                normalized,
                current,
                saved,
            )

            return self._ok(
                key=normalized,
                old_path=str(current),
                path=str(saved),
                restart_required=True,
            )
        except Exception as exc:
            return self._error(exc)

    def open_url(
        self,
        url: str,
    ) -> dict:
        try:
            if not url.startswith(
                ("https://", "http://")
            ):
                raise ValueError(
                    "Only HTTP/HTTPS links are allowed."
                )

            webbrowser.open(url)

            return self._ok()

        except Exception as exc:
            return self._error(exc)

    def about(self) -> dict:
        return self._ok(
            name=APP_FULL_NAME,
            version=APP_VERSION,
            author=AUTHOR,
            website=WEBSITE,
            repository=PUBLIC_REPOSITORY,
        )

    # --------------------------------------------------------
    # CAPTURE MODE
    # --------------------------------------------------------

    def clear_capture_geometry(self) -> dict:
        try:
            for key in (
                "capture_x",
                "capture_y",
                "capture_width",
                "capture_height",
            ):
                self._settings.delete(key)
            return self._ok(settings=self._settings.all())
        except Exception as exc:
            return self._error(exc)

    def open_capture_window(
        self,
        corner: str = "top-right",
        tutorial: bool = False,
    ) -> dict:
        """Open the proven separate Tk Capture Mode process safely."""
        try:
            main = self._require_main_window()

            saved_corner = self._settings.get(
                "capture_corner",
                "",
            ).strip()

            if saved_corner:
                corner = saved_corner

            existing = self._capture_process

            if existing is not None and existing.poll() is None:
                main.minimize()
                return self._ok(
                    mode="capture",
                    already_open=True,
                )

            left, top, right, bottom = self._main_monitor_work_area()

            if getattr(sys, "frozen", False):
                # Public Windows build: launch the same JAM.exe as a separate
                # process in Capture Mode. This preserves the proven separate
                # process architecture without shipping a second Python runtime.
                args = [
                    sys.executable,
                    "--capture",
                    "--corner",
                ]
            else:
                capture_script = Path(__file__).resolve().parent / "capture_app.py"

                if not capture_script.exists():
                    raise FileNotFoundError(
                        f"Missing Capture Mode file: {capture_script}"
                    )

                args = [
                    sys.executable,
                    str(capture_script),
                    "--corner",
                ]

            args.extend([
                str(corner or "top-right"),
                "--left",
                str(left),
                "--top",
                str(top),
                "--right",
                str(right),
                "--bottom",
                str(bottom),
            ])

            if bool(tutorial):
                args.append("--tutorial")

            creationflags = 0
            if os.name == "nt":
                creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)

            capture_log = LOG_DIR / "capture_process.log"
            capture_log.parent.mkdir(parents=True, exist_ok=True)
            log_handle = capture_log.open("a", encoding="utf-8", errors="replace")
            log_handle.write("\n=== Capture launch ===\n")
            log_handle.flush()

            try:
                process = subprocess.Popen(
                    args,
                    cwd=str(PROJECT_ROOT),
                    creationflags=creationflags,
                    stdout=log_handle,
                    stderr=log_handle,
                    text=True,
                )
            except Exception:
                log_handle.close()
                raise

            # Do not minimize JAM until Capture proves it actually started.
            # This prevents the half-second disappear/reappear regression when
            # the child process crashes during startup.
            time.sleep(0.30)

            if process.poll() is not None:
                log_handle.close()
                detail = "Capture Mode exited during startup."
                try:
                    lines = capture_log.read_text(
                        encoding="utf-8",
                        errors="replace",
                    ).splitlines()[-12:]
                    if lines:
                        detail += " " + " | ".join(line.strip() for line in lines if line.strip())
                except Exception:
                    pass
                raise RuntimeError(detail)

            self._capture_process = process
            self._shutting_down = False
            main.minimize()

            waiter = threading.Thread(
                target=self._wait_for_capture_process,
                args=(process,),
                name="JAM-Capture-Waiter",
                daemon=True,
            )
            waiter.start()
            self._capture_waiter = waiter

            self._settings.set(
                "capture_corner",
                corner,
            )

            logger.info(
                "Capture Mode process opened at %s",
                corner,
            )

            return self._ok(
                mode="capture",
                corner=corner,
            )

        except Exception as exc:
            return self._error(exc)

    def capture_window_status(self) -> dict:
        """Return whether the separate Capture Mode process is currently open."""
        try:
            process = self._capture_process
            is_open = bool(process is not None and process.poll() is None)
            return self._ok(open=is_open)
        except Exception as exc:
            return self._error(exc)

    def move_capture_window(
        self,
        corner: str,
    ) -> dict:
        """
        Kept for backward compatibility with older Capture HTML.
        The new native Capture process owns its own position selector.
        """
        try:
            self._settings.set(
                "capture_corner",
                corner,
            )
            return self._ok(
                corner=corner,
            )
        except Exception as exc:
            return self._error(exc)

    def close_capture_window(self) -> dict:
        """
        Optional programmatic close. Normally the user simply closes the
        Capture window itself; the process then exits and JAM restores.
        """
        try:
            process = self._capture_process

            if (
                process is not None
                and process.poll() is None
            ):
                process.terminate()

            return self._ok(
                mode="full",
            )

        except Exception as exc:
            return self._error(exc)
