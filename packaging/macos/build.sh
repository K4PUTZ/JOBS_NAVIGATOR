#!/usr/bin/env bash
set -euo pipefail

# Build a self-contained macOS bundle (PyInstaller onedir) and a double-clickable
# Terminal launcher (.command) for Sofa Jobs Navigator.
#
# Usage:
#   ./packaging/macos/build.sh
# Result:
#   dist/Sofa Jobs Navigator/            # Self-contained folder with Python + deps
#   dist/Sofa Jobs Navigator/Run.command # Double-click to open Terminal and run

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# Repo root is two levels up from this script
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$ROOT_DIR"

APP_NAME="Sofa Jobs Navigator"
ICON_ICNS="sofa_icon.icns"
ICON_PNG="sofa_icon.png"
HELP_DIR="src/sofa_jobs_navigator/ui/assets/help"

# MODE: app (GUI, .app bundle) or console (Terminal)
MODE="${MODE:-app}"
if [[ "${1:-}" == "--console" ]] || [[ "${1:-}" == "console" ]]; then
  MODE="console"
fi
echo "[mode] ${MODE}"

echo "[0/4] Cleaning previous build artifacts..."
rm -rf build dist "${APP_NAME}.spec"

echo "[1/4] Ensuring PyInstaller and project deps are installed..."
python3 -m pip install --upgrade pip wheel setuptools >/dev/null
python3 -m pip install --upgrade pyinstaller >/dev/null
# Install project so PyInstaller can resolve runtime deps from pyproject dependencies
python3 -m pip install --upgrade -e . >/dev/null

echo "[2/4] Running PyInstaller (onedir, ${MODE})..."
# Select UI flag
if [[ "$MODE" == "app" ]]; then
  UI_FLAG=(--windowed --osx-bundle-identifier com.sofaops.sofa-jobs-navigator)
else
  UI_FLAG=(--console)
fi
pyinstaller \
  --noconfirm \
  --clean \
  --onedir \
  "${UI_FLAG[@]}" \
  --name "$APP_NAME" \
  ${ICON_ICNS:+--icon "$ICON_ICNS"} \
  ${ICON_PNG:+--add-data "$ICON_PNG:."} \
  --add-data "$HELP_DIR/*.png:sofa_jobs_navigator/ui/assets/help" \
  --add-data "$HELP_DIR/README.md:sofa_jobs_navigator/ui/assets/help" \
  --collect-all googleapiclient \
  --collect-all google_auth_oauthlib \
  "run.py"

if [[ "$MODE" == "app" ]]; then
  APP_BUNDLE="dist/$APP_NAME.app"
  MACOS_DIR="$APP_BUNDLE/Contents/MacOS"
  BIN_PATH="$MACOS_DIR/$APP_NAME"
  DIST_DIR="dist/$APP_NAME.app"
else
  DIST_DIR="dist/$APP_NAME"
  BIN_PATH="$DIST_DIR/$APP_NAME"
fi

if [[ ! -e "$BIN_PATH" ]]; then
  echo "Build failed: missing binary at $BIN_PATH" >&2
  exit 1
fi

echo "[3/4] Creating launch helpers..."
if [[ "$MODE" == "app" ]]; then
  # Launchers that use `open` so Terminal is not required
  LAUNCHER="dist/Launch.command"
  cat >"$LAUNCHER" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
APP="Sofa Jobs Navigator.app"
DIR="$(cd "$(dirname "$0")" && pwd)"
open -n "$DIR/$APP" --args "$@"
SH
  chmod +x "$LAUNCHER"

  RESET_CMD="dist/Reset.command"
  cat >"$RESET_CMD" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
APP="Sofa Jobs Navigator.app"
DIR="$(cd "$(dirname "$0")" && pwd)"
open -n "$DIR/$APP" --args --factory-reset "$@"
SH
  chmod +x "$RESET_CMD"

  # Build a Launcher.app (separate name to avoid conflicts) using AppleScript
  if command -v osacompile >/dev/null 2>&1; then
    LAUNCHER_APP="dist/$APP_NAME Launcher.app"
    TMP_SCPT="dist/_launcher.scpt.txt"
    cat >"$TMP_SCPT" <<'APPLESCRIPT'
on run argv
  try
    set launcherApp to POSIX path of (path to me)
    set distDir to do shell script "dirname " & quoted form of launcherApp
    set appPath to distDir & "/Sofa Jobs Navigator.app"
    tell application "Terminal"
      activate
      do script "clear; echo '========================================'; echo '  Sofa Jobs Navigator'; echo '  Launching...'; echo '========================================'; sleep 1; exit" in (make new window)
    end tell
    delay 1.0
    do shell script "open -n " & quoted form of appPath
    delay 0.3
    try
      tell application "Sofa Jobs Navigator" to activate
    end try
    delay 0.3
    try
      tell application "Terminal" to close front window saving no
    end try
  end try
end run
APPLESCRIPT
    osacompile -o "$LAUNCHER_APP" "$TMP_SCPT"
    # Apply custom icon to launcher app
    if [[ -f "$ICON_ICNS" ]]; then
      cp "$ICON_ICNS" "$LAUNCHER_APP/Contents/Resources/applet.icns" || true
    fi
    rm -f "$TMP_SCPT"
  fi
else
  # Console mode launchers inside the folder
  LAUNCHER="$DIST_DIR/Run.command"
  cat >"$LAUNCHER" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
"$DIR/Sofa Jobs Navigator" "$@"
SH
  chmod +x "$LAUNCHER"
  RESET_CMD="$DIST_DIR/Reset.command"
  cat >"$RESET_CMD" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
"$DIR/Sofa Jobs Navigator" --factory-reset "$@"
SH
  chmod +x "$RESET_CMD"
fi

echo "[4/4] Writing quickstart README..."
cat >"$DIST_DIR/README-FIRST.txt" <<'TXT'
Sofa Jobs Navigator (macOS beta)
================================

How to run:
 - Double-click the app: Sofa Jobs Navigator.app (recommended), or
 - Double-click: Launch.command (runs the app via open), or
 - Terminal (console build only): cd into the folder and run: ./"Sofa Jobs Navigator"
 
 Reset preferences:
 - To clear preferences/tokens/logs any time, double-click: Reset.command
 
 First run (Google credentials):
 - Put your OAuth client JSON as credentials.json here:
   ~/Library/Application Support/sofa_jobs_navigator/credentials.json
   (Alternatively set env var SJN_CREDENTIALS_FILE=/path/to/credentials.json)

If macOS blocks the app (Gatekeeper):
- Right-click the app -> Open (confirm), or
- Remove quarantine: xattr -dr com.apple.quarantine "$(pwd)"

Logs:
- Open from the app menu, or see: ~/Library/Logs/sofa_jobs_navigator/console_log.txt

TXT

echo
echo "Build complete: $DIST_DIR"
echo "- Double-click: $LAUNCHER"
echo "- Or run: \"$BIN_PATH\""
