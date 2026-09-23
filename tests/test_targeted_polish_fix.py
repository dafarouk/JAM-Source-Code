from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_applications_edit_controls_and_double_click_exist():
    html = (ROOT / "ui" / "index.html").read_text(encoding="utf-8")
    js = (ROOT / "ui" / "js" / "app.js").read_text(encoding="utf-8")

    assert 'id="editSelectedBtn"' in html
    assert "function editSelectedApplication()" in js
    assert "'dblclick'" in js
    assert "openJobModal(app)" in js


def test_diagnostics_only_list_scrolls():
    js = (ROOT / "ui" / "js" / "batch1.js").read_text(encoding="utf-8")
    css = (ROOT / "ui" / "css" / "app.css").read_text(encoding="utf-8")

    assert "root.classList.add('diagnostics-modal')" in js
    assert ".diagnostics-modal .modal" in css
    assert "overflow: hidden" in css
    assert ".diagnostics-modal .diagnostic-list" in css
    assert "overflow-y: auto" in css


def test_capture_mode_has_work_mode():
    capture = (ROOT / "src" / "capture_app.py").read_text(encoding="utf-8")

    assert "self.work_mode_var" in capture
    assert '"work_mode": self._canonical_work_mode(self.work_mode_var.get())' in capture
    assert '"Onsite"' in capture
    assert '"Hybrid"' in capture
    assert '"Remote"' in capture


def test_sidebar_logo_is_stacked_and_large():
    css = (ROOT / "ui" / "css" / "app.css").read_text(encoding="utf-8")
    html = (ROOT / "ui" / "index.html").read_text(encoding="utf-8")

    assert "flex-direction: column" in css
    assert "width: 158px" in css
    assert "MADE BY FAROUK" in html
