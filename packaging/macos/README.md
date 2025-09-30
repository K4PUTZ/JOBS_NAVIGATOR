macOS Packaging (Beta)
======================

Goal: produce a self-contained folder that teammates can unzip and double-click to run (Terminal opens and shows output). No system Python required.

Prerequisites
- macOS host (builds must be done on macOS)
- Python 3.10+ installed on the build machine
- Internet for pip to fetch PyInstaller and dependencies

Build
- From repository root: ./packaging/macos/build.sh
- Output (app mode):
  - dist/Sofa Jobs Navigator.app   # app bundle to distribute
  - dist/Sofa Jobs Navigator.dmg   # compressed disk image with the app
  - dist/Sofa Jobs Navigator.dmg.sha256
  - dist/README-FIRST.txt          # quickstart

First Run (OAuth client)
- Place credentials.json at: ~/Library/Application Support/sofa_jobs_navigator/credentials.json
- Or set env var SJN_CREDENTIALS_FILE=/path/to/credentials.json before launching.

Gatekeeper (unsigned beta)
- First-time warning is expected. For the app bundle, right-click -> Open and confirm.
- For the DMG, some systems may still mark as quarantined. You can remove quarantine:
  xattr -dr com.apple.quarantine "dist/Sofa Jobs Navigator.dmg"

Notes
- The build uses PyInstaller onedir mode within the .app bundle to include the Python runtime and all required libraries (no separate Python install needed).
- Tk/ttk is bundled automatically via PyInstaller’s tkinter hook.
- Help assets and icons are included for in-app usage.
- For wider distribution, consider codesigning and notarization later.
