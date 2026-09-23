from __future__ import annotations

import sys
from pathlib import Path


def _run_capture_mode() -> bool:
    """Run Capture Mode inside a second JAM.exe process when requested."""
    if "--capture" not in sys.argv:
        return False

    # capture_app owns the rest of the command-line arguments. Remove only the
    # internal launcher flag so its existing argparse contract stays unchanged.
    sys.argv = [arg for arg in sys.argv if arg != "--capture"]

    from capture_app import main as capture_main

    capture_main()
    return True


def _startup_project_path() -> str | None:
    """Return a .jam file passed by Windows file association, if any."""
    for raw in sys.argv[1:]:
        if raw.startswith("-"):
            continue

        candidate = Path(raw).expanduser()
        if candidate.suffix.lower() != ".jam":
            continue

        try:
            if candidate.exists() and candidate.is_file():
                return str(candidate.resolve())
        except OSError:
            continue

    return None


def main() -> None:
    # This check intentionally happens before importing bridge/startup so the
    # lightweight Capture process does not pay for the full pywebview shell.
    if _run_capture_mode():
        return

    from bridge import JamApi
    from config import ensure_runtime_dirs
    from database import init_database
    from startup import launch_application

    ensure_runtime_dirs()
    init_database()

    bridge = JamApi(
        startup_project=_startup_project_path(),
    )
    launch_application(bridge)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        try:
            from app_logger import logger

            logger.exception("Fatal JAM startup error")
        except Exception:
            pass
        raise
