# Sofa Jobs Navigator

Lightweight desktop helper to jump between Google Drive SKU folders. Copy any text that contains a SKU, press `F12`, and pick from configurable favorites – the app resolves the matching Drive path, logs the activity, and optionally plays feedback sounds.

## Features
- Welcome window acts as the startup prompt; no separate connect prompt on launch. If not connected, the first search (F12) triggers Google sign-in automatically.
- Cross-platform (macOS, Linux, Windows) Tkinter UI with console log, favorites, and recent SKU list
- Modular architecture (reusable SKU detector, Drive client, clipboard reader, sound player)
- Configurable favorites and preferences stored per user with dry-run/testing flags
- Shortcut picker modal with number keys, clipboard parsing, and sound feedback
- Debug/test flags (set via environment variables):
  - `SJN_VERBOSE` – verbose logging
  - `SJN_OFFLINE` – disable live Drive calls (current default behaviour)
  - `SJN_CONFIG_DRY_RUN` – skip writing config during tests
  - `SJN_UI_DEBUG` – reserved for future UI diagnostics
  - `SJN_MUTE_SOUNDS` – silence audio cues
  - `SJN_MOCK_CLIPBOARD` – override clipboard content for automated tests
  - `SJN_TEST_HOTKEY` – remap the F12 launcher during tests

## Project Layout
```
JOBS NAVIGATOR/
├── README.md
├── pyproject.toml
├── DEVELOPMENT/
│   ├── MASTER_PLAN.md
│   ├── journal.json
│   └── packaging_notes.md
├── src/sofa_jobs_navigator/
│   ├── app.py
│   ├── config/
│   ├── controls/
│   ├── logging/
│   ├── services/
│   ├── ui/
│   └── utils/
└── tests/
```

## Running as a Script
1. Create a virtual environment and install dependencies:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
   pip install -e .[test]
   ```
2. Populate `src/sofa_jobs_navigator/config/reference_data.py` with your OAuth client values (`CREDENTIALS_TEMPLATE`).
3. Launch the tool (Auto-connect optional):
   ```bash
   python -m sofa_jobs_navigator.app
   ```
4. To connect: open **Settings → Connect / Refresh** or just press F12 to search — if not connected, the Google sign-in flow starts automatically. Tokens are cached under your user config directory.
5. You can enable **Connect on Startup** in Settings; otherwise, the app won't prompt on launch.

## Tests
Execute the automated suite once dependencies are installed:
```bash
pytest
```

## Packaging Overview
See `DEVELOPMENT/packaging_notes.md` for PyInstaller ideas and flag recommendations during builds. The `pyproject.toml` defines runtime and optional test dependencies.

## Reusing Modules
Each subsystem lives in its own module and carries ASCII separators plus context comments. Copy the desired module (for example, `utils/sku.py`) into other projects and import the functions/classes directly.

## Status & Next Steps
- Phase 1–3 complete; Phase 4 documentation in progress
- Master plan tracks detailed follow-up items inside `DEVELOPMENT/MASTER_PLAN.md`
