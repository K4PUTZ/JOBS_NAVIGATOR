# macOS Packaging — Sofa Jobs Navigator

Build a signed .app (unsigned by default) and optional .dmg using PyInstaller.

## Prerequisites
- Python 3.10+ with Tk (macOS python.org or Homebrew ok)
- Optional: `hdiutil` for DMG creation (preinstalled on macOS)
- Optional: `codesign` identity to sign the app after build

## Build Steps
1. Create/activate a venv and install runtime deps:
   - `python3 -m venv .venv && source .venv/bin/activate`
   - `pip install -e .` from `JOBS NAVIGATOR` (or `pip install -r requirements.txt` at repo root)
2. Run the packaging script:
   - `bash "JOBS NAVIGATOR/packaging/macos/build_mac.sh"`
   - The script auto-generates `sofa_icon.icns` from `sofa_icon.png` if missing (uses `sips` + `iconutil`).
3. Outputs:
   - App bundle: `JOBS NAVIGATOR/dist/Sofa Jobs Navigator.app`
   - DMG (if `hdiutil` present): `JOBS NAVIGATOR/dist/Sofa Jobs Navigator.dmg`

## Notes
- Icons: The app sets icons at runtime (PNG/ICO) via Tk; `.icns` is optional.
- Google client libs: A custom hook is included to pull in `googleapiclient` resources.
- First‑run setup: Use Settings → Connect/Refresh to authenticate; tokens are stored under user config via `platformdirs`.
- Offline mode builds: set `SJN_OFFLINE=1` to avoid live Google calls during smoke tests.
