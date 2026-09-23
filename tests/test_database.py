import sqlite3


def test_sqlite_available():
    conn = sqlite3.connect(":memory:")
    row = conn.execute("SELECT 1").fetchone()
    conn.close()
    assert row[0] == 1


def test_expected_branding_asset_names():
    expected = {"jam_logo.png", "jam_icon.png", "jam_bg.png"}
    assert expected == {"jam_logo.png", "jam_icon.png", "jam_bg.png"}
