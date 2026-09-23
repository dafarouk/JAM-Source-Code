from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from config import (  # noqa: E402
    APP_VERSION,
    GITHUB_REPOSITORY,
    SEMANTIC_MODEL_DIR,
)


def test_public_version_is_1_0_0() -> None:
    assert APP_VERSION == "1.0.0"
    assert GITHUB_REPOSITORY == "dafarouk/JAM"


def test_release_build_files_exist() -> None:
    required = [
        ROOT / "build" / "JAM.spec",
        ROOT / "build" / "JAM.iss",
        ROOT / "build" / "build_windows.ps1",
        ROOT / "build" / "release_windows.ps1",
        ROOT / "build" / "prepare_semantic_model.py",
        ROOT / "build" / "generate_version_info.py",
        ROOT / "build" / "README-FIRST.txt",
        ROOT / "build" / "README-FIRST.en.txt",
        ROOT / "build" / "README-FIRST.fr.txt",
        ROOT / "assets" / "setup" / "jam_setup_wizard.bmp",
        ROOT / "assets" / "setup" / "jam_setup_small.bmp",
    ]
    for path in required:
        assert path.exists(), path


def test_pyinstaller_spec_is_onedir_and_bundles_resources() -> None:
    spec = (ROOT / "build" / "JAM.spec").read_text(encoding="utf-8")
    assert "COLLECT(" in spec
    assert "exclude_binaries=True" in spec
    assert 'name="JAM"' in spec
    assert 'console=False' in spec
    assert '"ui"' in spec
    assert '"assets"' in spec
    assert '"runtime/models"' in spec
    assert "jam_runtime.ico" in spec


def test_installer_is_bilingual_branded_and_update_ready() -> None:
    iss = (ROOT / "build" / "JAM.iss").read_text(encoding="utf-8")
    assert 'Name: "english"' in iss
    assert 'Name: "french"' in iss
    assert "jam_setup_wizard.bmp" in iss
    assert "jam_setup_small.bmp" in iss
    assert "AppUpdatesURL=https://github.com/dafarouk/JAM/releases" in iss
    assert "Check: WizardSilent" in iss
    assert "CloseApplications=yes" in iss


def test_installer_has_shortcuts_and_jam_file_association() -> None:
    iss = (ROOT / "build" / "JAM.iss").read_text(encoding="utf-8")
    assert 'Name: "desktopicon"' in iss
    assert 'Name: "startmenuicon"' in iss
    assert 'Name: "fileassoc"' in iss
    assert "Software\\Classes\\.jam" in iss
    assert "JAM Project" in iss


def test_release_script_outputs_github_release_assets() -> None:
    script = (ROOT / "build" / "release_windows.ps1").read_text(encoding="utf-8")
    assert "JAM-Setup-$Version.exe" in script
    assert "JAM-v$Version-Windows-x64.zip" in script
    assert "SHA256.txt" in script
    assert "JAMInstallerBuild" in script
    assert "ISCC" in script


def test_packaged_capture_uses_same_executable_as_separate_process() -> None:
    main = (ROOT / "src" / "main.py").read_text(encoding="utf-8")
    bridge = (ROOT / "src" / "bridge.py").read_text(encoding="utf-8")
    assert '"--capture"' in main
    assert 'getattr(sys, "frozen", False)' in bridge
    assert '"--capture"' in bridge


def test_semantic_model_has_bundled_release_location() -> None:
    service = (ROOT / "src" / "services" / "semantic_match_service.py").read_text(
        encoding="utf-8"
    )
    assert SEMANTIC_MODEL_DIR.name == "paraphrase-multilingual-MiniLM-L12-v2"
    assert "SEMANTIC_MODEL_DIR.exists()" in service
    assert "prepare_semantic_model.py" in (
        ROOT / "build" / "build_windows.ps1"
    ).read_text(encoding="utf-8")
