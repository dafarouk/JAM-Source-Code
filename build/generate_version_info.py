from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "src" / "config.py"
OUTPUT = ROOT / "build" / "version_info.txt"


def read_version() -> str:
    text = CONFIG.read_text(encoding="utf-8")
    match = re.search(r'^APP_VERSION\s*=\s*"([^"]+)"', text, re.MULTILINE)
    if not match:
        raise RuntimeError("Unable to read APP_VERSION from src/config.py")
    return match.group(1)


def version_tuple(version: str) -> tuple[int, int, int, int]:
    numbers = []
    for part in version.split("."):
        match = re.match(r"(\d+)", part)
        numbers.append(int(match.group(1)) if match else 0)
    while len(numbers) < 4:
        numbers.append(0)
    return tuple(numbers[:4])


def main() -> None:
    version = read_version()
    filevers = version_tuple(version)

    content = f'''VSVersionInfo(
  ffi=FixedFileInfo(
    filevers={filevers},
    prodvers={filevers},
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable(
        '040904B0',
        [
          StringStruct('CompanyName', 'Farouk'),
          StringStruct('FileDescription', 'JAM - Job Application Manager'),
          StringStruct('FileVersion', '{version}'),
          StringStruct('InternalName', 'JAM'),
          StringStruct('OriginalFilename', 'JAM.exe'),
          StringStruct('ProductName', 'JAM - Job Application Manager'),
          StringStruct('ProductVersion', '{version}')
        ]
      )
    ]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
'''
    OUTPUT.write_text(content, encoding="utf-8")
    print(f"Generated {OUTPUT} for JAM {version}")


if __name__ == "__main__":
    main()
