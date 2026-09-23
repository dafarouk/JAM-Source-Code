# JAM - Job Application Manager

JAM is a local-first Windows desktop application for tracking job opportunities, applications, interviews, contacts, follow-ups, exports and CV/job matching.

## Development version

`0.1.0`

## Stack

- Python 3.11
- pywebview
- HTML / CSS / Vanilla JavaScript
- SQLite
- PyMuPDF
- python-docx
- openpyxl
- ReportLab
- pytest

## Current foundation

- Premium JAM/CVM-family desktop shell
- Branded splash screen
- Dashboard KPIs
- Applications table
- Quick Capture Mode with always-on-top window behavior
- Add/edit/delete and bulk delete
- Status pipeline
- Automatic saved/applied timestamps
- Local deterministic CV/job match engine
- PDF/DOCX/TXT/readable `.cvm` CV input
- Excel and PDF exports
- Export history
- `.jam` portable project save/open
- Recent projects
- Local database backup
- Logs viewer
- Contact / Support / About JAM
- Double-confirm reset flow handled in the UI

## Branding assets expected

Keep your existing files under `assets/branding/`:

- `jam_logo.png`
- `jam_icon.png`
- `jam_bg.png`

The Windows `.ico` asset comes later.

## Run

```powershell
py -3.11 -m venv .venv
Set-ExecutionPolicy -Scope Process Bypass -Force
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python src\main.py
```

## Test

```powershell
pytest -q
```

## Local data

Runtime data: `%LOCALAPPDATA%\Farouk\JAM\`

Exports: `%USERPROFILE%\Documents\JAM Exports`

Portable projects: `%USERPROFILE%\Documents\JAM Projects`


## Current UX additions

- Smooth compact Capture Mode scrolling
- Branded Excel/PDF exports with filter context
- Excel application import with flexible column matching
- Draggable Pipeline board with direct deletion
- Searchable salary currency selector
- Friendly diagnostics/log viewer and visible support links
- Dedicated Guide page placeholder
