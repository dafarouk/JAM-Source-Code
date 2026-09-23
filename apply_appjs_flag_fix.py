from __future__ import annotations

from pathlib import Path
import shutil
import sys


def main() -> int:
    root = Path(__file__).resolve().parent
    app_js = root / "ui" / "js" / "app.js"

    if not app_js.exists():
        print(f"ERROR: Could not find {app_js}")
        print("Place this script in the JAM project root, next to src/ and ui/.")
        return 1

    text = app_js.read_text(encoding="utf-8")
    original = text

    replacements = {
        "https://flagcdn.com/w40/${currency.country}.png":
            "../assets/flags/${currency.country}.png",
        "https://flagcdn.com/w80/${currency.country}.png":
            "../assets/flags/${currency.country}.png",
        "https://flagcdn.com/w20/${currency.country}.png":
            "../assets/flags/${currency.country}.png",
    }

    for source, target in replacements.items():
        text = text.replace(source, target)

    if "flagcdn.com" in text:
        print("ERROR: app.js still contains another flagcdn.com reference.")
        print("No file was changed. Send me that line and I will patch that exact variant.")
        return 2

    if text == original:
        print("app.js is already using local currency flags. Nothing to change.")
        return 0

    backup = app_js.with_suffix(".js.before_local_flags.bak")
    if not backup.exists():
        shutil.copy2(app_js, backup)

    app_js.write_text(text, encoding="utf-8")
    print("Fixed ui/js/app.js: FlagCDN dependency replaced with assets/flags/*.png")
    print(f"Backup: {backup}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
