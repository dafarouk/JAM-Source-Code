from __future__ import annotations

import ast
import shutil
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def test_required_scripts_are_loaded_in_safe_order():
    html = (ROOT / "ui" / "index.html").read_text(encoding="utf-8")

    app_index = html.index('src="js/app.js"')
    i18n_index = html.index('src="js/i18n.js"')
    batch_index = html.index('src="js/batch1.js"')

    assert app_index < i18n_index < batch_index


def test_i18n_observer_does_not_watch_its_own_text_or_attributes():
    source = (ROOT / "ui" / "js" / "i18n.js").read_text(encoding="utf-8")

    observer_start = source.index("function installMutationObserver()")
    observer_end = source.index("function installFunctionOverrides()")
    observer = source[observer_start:observer_end]

    assert "characterData: true" not in observer
    assert "attributes: true" not in observer
    assert "childList: true" in observer


def test_offline_currency_flags_exist_and_no_runtime_flagcdn_dependency():
    flags_dir = ROOT / "assets" / "flags"
    expected = {
        "eu", "us", "tn", "ma", "dz", "ly", "eg", "sa", "ae", "qa",
        "kw", "bh", "om", "jo", "lb", "iq", "tr", "gb", "ca", "ch",
    }

    present = {path.stem for path in flags_dir.glob("*.png")}
    assert expected.issubset(present)

    combined = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in (ROOT / "ui").rglob("*.js")
    )
    assert "flagcdn.com" not in combined


def test_bridge_exposes_foundation_safety_api():
    tree = ast.parse((ROOT / "src" / "bridge.py").read_text(encoding="utf-8"))
    method_names = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
    }

    expected = {
        "list_backups",
        "restore_backup",
        "save_draft",
        "get_draft",
        "clear_draft",
        "project_state",
        "save_current_project",
        "discard_project_changes",
        "restore_project_recovery",
        "discard_project_recovery",
        "run_diagnostics",
        "open_data_location",
        "handle_close_request",
    }

    assert expected.issubset(method_names)


def test_batch1_frontend_contains_foundation_features():
    source = (ROOT / "ui" / "js" / "batch1.js").read_text(encoding="utf-8")

    required_markers = (
        "installOfflineCurrencyFlags",
        "installArchiveBehavior",
        "installMainDraftAutosave",
        "installDirtyProjectGuards",
        "showBackupRestore",
        "runDiagnostics",
        "injectDataLocations",
        "promptProjectRecovery",
    )

    for marker in required_markers:
        assert marker in source


def test_all_python_source_parses():
    for path in (ROOT / "src").rglob("*.py"):
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def test_all_javascript_passes_node_syntax_check():
    node = shutil.which("node")
    if not node:
        pytest.skip("Node.js is not installed in this test environment.")

    for path in (ROOT / "ui" / "js").glob("*.js"):
        result = subprocess.run(
            [node, "--check", str(path)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr


def test_static_index_text_has_french_translation_coverage():
    import re
    from html.parser import HTMLParser

    class VisibleTextParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.skip = 0
            self.values = []

        def handle_starttag(self, tag, attrs):
            if tag in {"script", "style"}:
                self.skip += 1

        def handle_endtag(self, tag):
            if tag in {"script", "style"} and self.skip:
                self.skip -= 1

        def handle_data(self, data):
            if not self.skip:
                text = " ".join(data.split())
                if text:
                    self.values.append(text)

    parser = VisibleTextParser()
    parser.feed((ROOT / "ui" / "index.html").read_text(encoding="utf-8"))

    i18n = (ROOT / "ui" / "js" / "i18n.js").read_text(encoding="utf-8")
    key_matches = re.findall(
        r'''^\s*(?:'((?:\\'|[^'])+)'|"((?:\\"|[^"])+)")\s*:''',
        i18n,
        re.M,
    )
    keys = {left or right for left, right in key_matches}

    allow = {
        "JAM",
        "Job Application Manager",
        "JAM - Job Application Manager",
        "BY FAROUK",
        "Pipeline",
        "Exports",
        "Guide",
        "Contact",
        "PayPal",
        "Ko-fi",
        "Data Analyst",
        "LinkedIn",
        "Paris",
        "★",
        "★★",
        "★★★",
        "★★★★",
        "★★★★★",
        "×",
        "⌂",
        "▤",
        "◫",
        "◎",
        "⇩",
        "⚙",
        "?",
        "0",
        "0%",
        "JAM Guide",
    }

    regex_covered = {"0 selected"}

    missing = {
        text
        for text in parser.values
        if re.search(r"[A-Za-z]", text)
        and text not in allow
        and text not in regex_covered
        and text not in keys
    }

    assert not missing, sorted(missing)
