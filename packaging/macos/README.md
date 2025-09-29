macOS Packaging (Beta)
======================

Goal: produce a self-contained folder that teammates can unzip and double-click to run (Terminal opens and shows output). No system Python required.

Prerequisites
- macOS host (builds must be done on macOS)
- Python 3.10+ installed on the build machine
- Internet for pip to fetch PyInstaller and dependencies

Build
- From repository root: ./packaging/macos/build.sh
- Output: dist/Sofa Jobs Navigator/
  - Sofa Jobs Navigator        # bundled executable (Python + deps included)
  - Run.command                # double-click to open Terminal and start the app
  - README-FIRST.txt           # quickstart

First Run (OAuth client)
- Place credentials.json at: ~/Library/Application Support/sofa_jobs_navigator/credentials.json
- Or set env var SJN_CREDENTIALS_FILE=/path/to/credentials.json before launching.

Gatekeeper (unsigned beta)
- First-time warning is expected. Right-click Run.command -> Open and confirm, or remove quarantine:
  xattr -dr com.apple.quarantine "dist/Sofa Jobs Navigator"

Notes
- The build uses PyInstaller onedir mode to include the Python runtime and all required libraries (no separate Python install needed).
- Tk/ttk is bundled automatically via PyInstaller’s tkinter hook.
- Help assets and icons are included for in-app usage.
- For wider distribution, consider codesigning and notarization later.

