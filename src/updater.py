from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from packaging.version import InvalidVersion, Version

from config import (
    APP_FULL_NAME,
    APP_VERSION,
    GITHUB_REPOSITORY,
    UPDATE_CACHE_FILE,
    UPDATE_CHECK_INTERVAL_HOURS,
    UPDATE_DOWNLOAD_DIR,
    UPDATE_HASH_ASSET_NAME,
    UPDATE_PENDING_FILE,
)


class Updater:
    """GitHub Releases updater used by public JAM Windows builds.

    The service deliberately mirrors the proven CV Maker release model:
    GitHub Releases are the source of truth, Setup EXE assets are verified by
    SHA-256, downloads use a temporary .part file, and the Inno Setup installer
    is launched silently so the installed build can replace the running one and
    restart JAM.
    """

    def __init__(self) -> None:
        UPDATE_DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
        self._progress_lock = threading.Lock()
        self._download_thread: threading.Thread | None = None
        self._progress: dict[str, Any] = self._idle_progress()
        self._cleanup_downloads()

    # ========================================================
    # STATE / HELPERS
    # ========================================================

    @staticmethod
    def _idle_progress() -> dict[str, Any]:
        return {
            "phase": "idle",
            "percent": 0,
            "downloaded_bytes": 0,
            "total_bytes": 0,
            "message": "",
            "version": "",
            "notes": "",
            "path": "",
            "error": "",
        }

    def _set_progress(self, **changes: Any) -> None:
        with self._progress_lock:
            self._progress.update(changes)

    def progress(self) -> dict[str, Any]:
        with self._progress_lock:
            return dict(self._progress)

    def status(self) -> dict[str, Any]:
        return {
            "enabled": bool(GITHUB_REPOSITORY),
            "current_version": APP_VERSION,
            "repository": GITHUB_REPOSITORY,
            "check_interval_hours": UPDATE_CHECK_INTERVAL_HOURS,
            "progress": self.progress(),
            "completed_update": self.completed_update(),
        }

    @staticmethod
    def _read_json(path: Path, fallback: Any) -> Any:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return fallback

    @staticmethod
    def _write_json(path: Path, payload: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_suffix(path.suffix + ".tmp")
        temp.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temp.replace(path)

    @staticmethod
    def _version(value: str) -> Version | None:
        text = str(value or "").strip().lstrip("vV")
        try:
            return Version(text)
        except InvalidVersion:
            return None

    @staticmethod
    def _asset_by_name(assets: list[dict], name: str) -> dict | None:
        wanted = name.casefold()
        for asset in assets:
            if str(asset.get("name", "")).casefold() == wanted:
                return asset
        return None

    @staticmethod
    def _setup_asset(assets: list[dict], version: str) -> dict | None:
        exact_name = f"JAM-Setup-{version}.exe"
        exact = Updater._asset_by_name(assets, exact_name)
        if exact:
            return exact

        candidates = []
        for asset in assets:
            name = str(asset.get("name", ""))
            lowered = name.casefold()
            if (
                lowered.endswith(".exe")
                and "jam" in lowered
                and "setup" in lowered
            ):
                candidates.append(asset)

        return candidates[0] if len(candidates) == 1 else None

    @staticmethod
    def _release_note_items(notes: str) -> list[str]:
        items: list[str] = []
        for raw in str(notes or "").splitlines():
            line = raw.strip()
            if not line:
                continue
            match = re.match(r"^(?:[-*•]|\d+[.)])\s+(.+)$", line)
            if not match:
                continue
            value = match.group(1).strip()
            if value and value not in items:
                items.append(value)
        return items[:30]

    @staticmethod
    def _github_headers() -> dict[str, str]:
        return {
            "Accept": "application/vnd.github+json",
            "User-Agent": f"{APP_FULL_NAME}/{APP_VERSION}",
        }

    def _cleanup_downloads(self) -> None:
        for partial in UPDATE_DOWNLOAD_DIR.glob("*.part"):
            try:
                partial.unlink()
            except OSError:
                pass

        current = self._version(APP_VERSION)
        if current is None:
            return

        pattern = re.compile(
            r"^JAM-Setup-v?(?P<version>.+)\.exe$",
            flags=re.IGNORECASE,
        )

        for installer in UPDATE_DOWNLOAD_DIR.glob("JAM-Setup-*.exe"):
            match = pattern.match(installer.name)
            if not match:
                continue

            version = self._version(match.group("version"))
            if version is None or version > current:
                continue

            try:
                installer.unlink()
            except OSError:
                # The previous updater/installer may still be finishing.
                pass

    # ========================================================
    # RELEASE CHECK
    # ========================================================

    def _fetch_latest_release(self) -> dict[str, Any]:
        if not GITHUB_REPOSITORY:
            return {
                "ok": False,
                "configured": False,
                "message": "GitHub repository is not configured yet.",
            }

        url = f"https://api.github.com/repos/{GITHUB_REPOSITORY}/releases/latest"
        request = urllib.request.Request(url, headers=self._github_headers())

        try:
            with urllib.request.urlopen(request, timeout=8) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return {
                    "ok": False,
                    "configured": True,
                    "message": "No public JAM GitHub Release exists yet.",
                }
            return {
                "ok": False,
                "configured": True,
                "message": f"GitHub returned HTTP {exc.code}.",
            }
        except (urllib.error.URLError, TimeoutError, ValueError) as exc:
            return {
                "ok": False,
                "configured": True,
                "message": f"Unable to contact GitHub: {exc}",
            }

        latest_text = str(payload.get("tag_name", "")).strip().lstrip("vV")
        latest_version = self._version(latest_text)
        current_version = self._version(APP_VERSION)

        if latest_version is None:
            return {
                "ok": False,
                "configured": True,
                "message": "The latest GitHub Release has an invalid version tag.",
            }

        if current_version is None:
            return {
                "ok": False,
                "configured": True,
                "message": "The current JAM version is invalid.",
            }

        assets = payload.get("assets") or []
        setup = self._setup_asset(assets, latest_text)
        hashes = self._asset_by_name(assets, UPDATE_HASH_ASSET_NAME)

        setup_digest = ""
        if setup:
            digest = str(setup.get("digest", "") or "")
            if digest.lower().startswith("sha256:"):
                setup_digest = digest.split(":", 1)[1].strip().lower()

        available = latest_version > current_version
        install_ready = bool(
            available
            and setup
            and setup.get("browser_download_url")
            and (setup_digest or hashes)
        )

        return {
            "ok": True,
            "configured": True,
            "current": APP_VERSION,
            "latest": latest_text,
            "available": available,
            "name": str(payload.get("name") or f"JAM {latest_text}"),
            "notes": str(payload.get("body") or "").strip(),
            "note_items": self._release_note_items(str(payload.get("body") or "")),
            "published_at": str(payload.get("published_at") or ""),
            "release_url": str(payload.get("html_url") or ""),
            "setup_name": str(setup.get("name") or "") if setup else "",
            "setup_url": str(setup.get("browser_download_url") or "") if setup else "",
            "setup_size": int(setup.get("size") or 0) if setup else 0,
            "setup_digest": setup_digest,
            "hash_url": str(hashes.get("browser_download_url") or "") if hashes else "",
            "install_ready": install_ready,
        }

    def check(self, manual: bool = False) -> dict[str, Any]:
        if not GITHUB_REPOSITORY:
            return {
                "ok": False,
                "configured": False,
                "message": "GitHub repository is not configured yet.",
            }

        cache = self._read_json(UPDATE_CACHE_FILE, {})
        now = time.time()
        interval_seconds = max(1, UPDATE_CHECK_INTERVAL_HOURS) * 3600
        last_checked = float(cache.get("last_checked") or 0)

        if (
            not manual
            and last_checked > 0
            and (now - last_checked) < interval_seconds
        ):
            return {
                "ok": True,
                "configured": True,
                "skipped": True,
                "available": False,
                "current": APP_VERSION,
                "next_check_in_seconds": int(
                    max(0, interval_seconds - (now - last_checked))
                ),
            }

        result = self._fetch_latest_release()

        if result.get("ok"):
            self._write_json(
                UPDATE_CACHE_FILE,
                {
                    "last_checked": now,
                    "current": APP_VERSION,
                    "latest": result.get("latest", ""),
                    "available": bool(result.get("available")),
                },
            )

        return result

    # ========================================================
    # DOWNLOAD + VERIFICATION
    # ========================================================

    def _download_text(self, url: str) -> str:
        request = urllib.request.Request(
            url,
            headers={"User-Agent": f"{APP_FULL_NAME}/{APP_VERSION}"},
        )
        with urllib.request.urlopen(request, timeout=15) as response:
            return response.read().decode("utf-8", errors="replace")

    def _expected_hash_from_file(self, url: str, setup_name: str) -> str:
        if not url:
            return ""

        try:
            content = self._download_text(url)
        except Exception:
            return ""

        setup_lower = setup_name.casefold()
        for line in content.splitlines():
            stripped = line.strip()
            if not stripped or setup_lower not in stripped.casefold():
                continue

            match = re.match(r"^([0-9a-fA-F]{64})\s+", stripped)
            if match:
                return match.group(1).lower()

        return ""

    def start_download(self) -> dict[str, Any]:
        with self._progress_lock:
            if self._download_thread and self._download_thread.is_alive():
                return {
                    "ok": False,
                    "message": "An update download is already running.",
                    "progress": dict(self._progress),
                }

        release = self._fetch_latest_release()
        if not release.get("ok"):
            return release

        if not release.get("available"):
            return {
                "ok": False,
                "message": "JAM is already up to date.",
            }

        if not release.get("install_ready"):
            return {
                "ok": False,
                "message": (
                    "The latest release is missing the JAM Setup EXE or SHA-256 proof."
                ),
                "release_url": release.get("release_url", ""),
            }

        self._progress = self._idle_progress()
        self._set_progress(
            phase="starting",
            message="Preparing update download…",
            version=str(release.get("latest") or ""),
            notes=str(release.get("notes") or ""),
            total_bytes=int(release.get("setup_size") or 0),
        )

        worker = threading.Thread(
            target=self._download_worker,
            args=(release,),
            daemon=True,
            name="jam-update-download",
        )
        self._download_thread = worker
        worker.start()

        return {
            "ok": True,
            "started": True,
            "version": release.get("latest", ""),
            "progress": self.progress(),
        }

    def _download_worker(self, release: dict[str, Any]) -> None:
        setup_url = str(release.get("setup_url") or "")
        setup_name = str(release.get("setup_name") or "")
        total_bytes = int(release.get("setup_size") or 0)

        expected_hash = str(release.get("setup_digest") or "").lower()
        if not expected_hash:
            expected_hash = self._expected_hash_from_file(
                str(release.get("hash_url") or ""),
                setup_name,
            )

        if not expected_hash:
            self._set_progress(
                phase="error",
                error="The update checksum is missing.",
                message="The update could not be verified.",
            )
            return

        for old in UPDATE_DOWNLOAD_DIR.glob("JAM-Setup-*.exe"):
            try:
                old.unlink()
            except OSError:
                pass

        target = UPDATE_DOWNLOAD_DIR / setup_name
        partial = target.with_suffix(target.suffix + ".part")
        try:
            partial.unlink(missing_ok=True)
        except OSError:
            pass

        digest = hashlib.sha256()
        request = urllib.request.Request(
            setup_url,
            headers={"User-Agent": f"{APP_FULL_NAME}/{APP_VERSION}"},
        )

        self._set_progress(
            phase="downloading",
            message="Downloading JAM update…",
            percent=0,
            downloaded_bytes=0,
            total_bytes=total_bytes,
        )

        downloaded = 0
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                if total_bytes <= 0:
                    try:
                        total_bytes = int(response.headers.get("Content-Length") or 0)
                    except (TypeError, ValueError):
                        total_bytes = 0

                with partial.open("wb") as handle:
                    while True:
                        chunk = response.read(1024 * 1024)
                        if not chunk:
                            break
                        handle.write(chunk)
                        digest.update(chunk)
                        downloaded += len(chunk)

                        percent = 0
                        if total_bytes > 0:
                            percent = max(
                                0,
                                min(99, int((downloaded / total_bytes) * 100)),
                            )

                        self._set_progress(
                            phase="downloading",
                            percent=percent,
                            downloaded_bytes=downloaded,
                            total_bytes=total_bytes,
                            message="Downloading JAM update…",
                        )
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            try:
                partial.unlink(missing_ok=True)
            except OSError:
                pass
            self._set_progress(
                phase="error",
                error=str(exc),
                message=f"Update download failed: {exc}",
            )
            return

        self._set_progress(
            phase="verifying",
            percent=99,
            downloaded_bytes=downloaded,
            total_bytes=total_bytes or downloaded,
            message="Verifying SHA-256…",
        )

        actual_hash = digest.hexdigest().lower()
        if actual_hash != expected_hash:
            try:
                partial.unlink(missing_ok=True)
            except OSError:
                pass
            self._set_progress(
                phase="error",
                error="sha256_mismatch",
                message="The downloaded update failed SHA-256 verification.",
            )
            return

        partial.replace(target)

        self._set_progress(
            phase="ready",
            percent=100,
            downloaded_bytes=downloaded,
            total_bytes=total_bytes or downloaded,
            message="Download verified. Ready to install.",
            path=str(target),
            version=str(release.get("latest") or ""),
            notes=str(release.get("notes") or ""),
            error="",
        )

    # ========================================================
    # INSTALL / POST-UPDATE
    # ========================================================

    def install_downloaded(self) -> dict[str, Any]:
        progress = self.progress()
        if progress.get("phase") != "ready":
            return {
                "ok": False,
                "message": "The update is not ready to install yet.",
            }

        if sys.platform != "win32":
            return {
                "ok": False,
                "message": "Automatic installation is available on Windows only.",
            }

        try:
            path = Path(str(progress.get("path") or "")).expanduser().resolve()
            root = UPDATE_DOWNLOAD_DIR.resolve()
        except OSError:
            return {
                "ok": False,
                "message": "The downloaded installer path is invalid.",
            }

        try:
            path.relative_to(root)
        except ValueError:
            return {
                "ok": False,
                "message": "JAM refused to launch an installer outside its update folder.",
            }

        if not path.exists() or path.suffix.lower() != ".exe":
            return {
                "ok": False,
                "message": "The downloaded JAM installer could not be found.",
            }

        target_version = str(progress.get("version") or "").strip()
        notes = str(progress.get("notes") or "")
        pending = {
            "from_version": APP_VERSION,
            "target_version": target_version,
            "notes": notes,
            "items": self._release_note_items(notes),
            "started_at": time.time(),
        }
        self._write_json(UPDATE_PENDING_FILE, pending)

        creationflags = 0
        creationflags |= getattr(subprocess, "DETACHED_PROCESS", 0)
        creationflags |= getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)

        try:
            subprocess.Popen(
                [
                    str(path),
                    "/VERYSILENT",
                    "/SUPPRESSMSGBOXES",
                    "/NORESTART",
                    "/CLOSEAPPLICATIONS",
                ],
                cwd=str(path.parent),
                close_fds=True,
                creationflags=creationflags,
            )
        except OSError as exc:
            try:
                UPDATE_PENDING_FILE.unlink(missing_ok=True)
            except OSError:
                pass
            return {
                "ok": False,
                "message": f"Unable to start the update installer: {exc}",
            }

        self._set_progress(
            phase="installing",
            percent=100,
            message=(
                "Installer started. JAM will close and restart automatically. "
                "Do not reopen JAM manually."
            ),
        )

        return {
            "ok": True,
            "message": "The JAM update installer was started.",
            "version": target_version,
        }

    def completed_update(self) -> dict[str, Any] | None:
        pending = self._read_json(UPDATE_PENDING_FILE, None)
        if not isinstance(pending, dict):
            return None

        target_text = str(pending.get("target_version") or "").strip()
        target_version = self._version(target_text)
        current_version = self._version(APP_VERSION)
        if target_version is None or current_version is None:
            return None

        if current_version < target_version:
            # Installation has not successfully reached the requested build yet.
            return None

        items = pending.get("items")
        if not isinstance(items, list):
            items = self._release_note_items(str(pending.get("notes") or ""))

        return {
            "version": APP_VERSION,
            "target_version": target_text,
            "from_version": str(pending.get("from_version") or ""),
            "notes": str(pending.get("notes") or ""),
            "items": [str(item) for item in items if str(item).strip()][:30],
        }

    def acknowledge_completed_update(self) -> None:
        completed = self.completed_update()
        if not completed:
            return

        try:
            UPDATE_PENDING_FILE.unlink(missing_ok=True)
        except OSError:
            pass

        # Force the normal automatic checker to wait for the next interval.
        cache = self._read_json(UPDATE_CACHE_FILE, {})
        cache.update(
            {
                "last_checked": time.time(),
                "current": APP_VERSION,
                "latest": APP_VERSION,
                "available": False,
            }
        )
        self._write_json(UPDATE_CACHE_FILE, cache)
