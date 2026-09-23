from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_batch2_script_is_loaded_after_existing_layers():
    html = (ROOT / "ui" / "index.html").read_text(encoding="utf-8")
    assert '<script src="js/settings_polish.js"></script>' in html
    assert '<script src="js/batch2.js"></script>' in html
    assert html.index('js/batch2.js') > html.index('js/settings_polish.js')


def test_batch2_ui_contains_core_workflows():
    js = (ROOT / "ui" / "js" / "batch2.js").read_text(encoding="utf-8")
    for token in (
        "check_duplicates",
        "get_application_details",
        "bulk_update_applications",
        "preview_excel_dialog",
        "confirm_excel_import",
        "save_view",
        "remove_export_history",
        "remove_recent_project",
        "salary_min",
        "status_history",
    ):
        assert token in js
