from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_analyzer_hotfix_loaded_after_batch1():
    html = (ROOT / "ui" / "index.html").read_text(encoding="utf-8")
    assert '<script src="js/analyzer_hotfix.js"></script>' in html
    assert html.index('js/batch1.js') < html.index('js/analyzer_hotfix.js')


def test_analyzer_controls_exist():
    html = (ROOT / "ui" / "index.html").read_text(encoding="utf-8")
    for element_id in (
        "previewCvBtn",
        "clearAnalyzerBtn",
        "saveAnalyzerResultBtn",
        "analyzerHistoryList",
    ):
        assert f'id="{element_id}"' in html


def test_excel_dialog_uses_single_valid_filter():
    bridge = (ROOT / "src" / "bridge.py").read_text(encoding="utf-8")
    assert 'Excel files (*.xlsx;*.xlsm)' in bridge
    assert 'Excel Macro-Enabled Workbook (*.xlsm)' not in bridge


def test_capture_startup_health_check_present():
    bridge = (ROOT / "src" / "bridge.py").read_text(encoding="utf-8")
    assert 'capture_process.log' in bridge
    assert 'time.sleep(0.30)' in bridge
    assert 'Capture Mode exited during startup.' in bridge
