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

echo "[3/5] Creating launch helpers..."
if [[ "$MODE" == "app" ]]; then
  # Keep it simple: only the .app bundle is produced (no extra launchers).
  :
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

echo "[4/5] Applying bundle metadata and writing quickstart README..."
# Inject version into the app's Info.plist (Finder shows it)
if [[ "$MODE" == "app" ]]; then
  VERSION_PY="src/sofa_jobs_navigator/version.py"
  if [[ -f "$VERSION_PY" ]]; then
    VERSION=$(python3 -c "import re,pathlib; p=pathlib.Path('src/sofa_jobs_navigator/version.py').read_text(encoding='utf-8'); m=re.search(r'^VERSION(?:\\s*:\\s*[^=]+)?\\s*=\\s*[\\\"\\\']([^\\\"\\\']+)[\\\"\\\']', p, flags=re.M); print(m.group(1) if m else '0.0.0')" 2>/dev/null || echo '0.0.0')
    INFO_PLIST="$APP_BUNDLE/Contents/Info.plist"
    if [[ -f "$INFO_PLIST" ]]; then
      if command -v /usr/libexec/PlistBuddy >/dev/null 2>&1; then
        /usr/libexec/PlistBuddy -c "Set :CFBundleShortVersionString $VERSION" "$INFO_PLIST" 2>/dev/null || \
        /usr/libexec/PlistBuddy -c "Add :CFBundleShortVersionString string $VERSION" "$INFO_PLIST"
        /usr/libexec/PlistBuddy -c "Set :CFBundleVersion $VERSION" "$INFO_PLIST" 2>/dev/null || \
        /usr/libexec/PlistBuddy -c "Add :CFBundleVersion string $VERSION" "$INFO_PLIST"
      else
        defaults write "${INFO_PLIST%.plist}" CFBundleShortVersionString "$VERSION" || true
        defaults write "${INFO_PLIST%.plist}" CFBundleVersion "$VERSION" || true
      fi
      echo "[info] Set app version to $VERSION in Info.plist"
    fi
  fi
fi
cat >"$DIST_DIR/README-FIRST.txt" <<'TXT'
Sofa Jobs Navigator (macOS beta)
================================

How to run:
 - Double-click the app: Sofa Jobs Navigator.app (recommended)
 - Console build only: cd into the folder and run: ./"Sofa Jobs Navigator"
 
 Reset preferences:
 - In-app: use the Reset option from the menu
 - Terminal: open -n "Sofa Jobs Navigator.app" --args --factory-reset
 
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
echo "[5/5] Creating DMG..."
if [[ "$MODE" == "app" ]]; then
  DMG_PATH="dist/$APP_NAME.dmg"
  hdiutil create -volname "$APP_NAME" -srcfolder "$APP_BUNDLE" -ov -format UDZO "$DMG_PATH" >/dev/null
  if command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$DMG_PATH" > "${DMG_PATH}.sha256"
  fi
fi

echo
echo "Build complete: $DIST_DIR"
if [[ "$MODE" == "app" ]]; then
  echo "- Double-click the app bundle to launch."
  echo "- DMG: $(basename "$DMG_PATH")"
else
  echo "- Double-click: $LAUNCHER"
  echo "- Or run: \"$BIN_PATH\""
fi
