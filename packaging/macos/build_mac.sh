#!/usr/bin/env bash
set -euo pipefail

# Build macOS .app bundle for Sofa Jobs Navigator using PyInstaller
# Produces: dist/Sofa Jobs Navigator.app and optional DMG if hdiutil is available.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="${SCRIPT_DIR}/../../.."
APP_DIR="${ROOT_DIR}/JOBS NAVIGATOR"

cd "${APP_DIR}"

if ! command -v pyinstaller >/dev/null 2>&1; then
  echo "[i] Installing pyinstaller..."
  python3 -m pip install --upgrade pip
  python3 -m pip install pyinstaller
fi

ensure_icns() {
  local out_icns="${APP_DIR}/sofa_icon.icns"
  # If an .icns already exists, keep it
  if [[ -f "${out_icns}" ]]; then
    echo "[i] Found existing .icns: ${out_icns}"
    return 0
  fi
  # Pick the best source PNG available
  local -a png_candidates=(
    "${APP_DIR}/sofa_icon_1024.png"
    "${APP_DIR}/sofa_icon.png"
    "${APP_DIR}/DRIVE_OPERATOR/sofa_icon_1024.png"
    "${APP_DIR}/DRIVE_OPERATOR/sofa_icon.png"
  )
  local src_png=""
  for p in "${png_candidates[@]}"; do
    if [[ -f "${p}" ]]; then src_png="${p}"; break; fi
  done
  if [[ -z "${src_png}" ]]; then
    echo "[!] No source PNG found for .icns generation (looked for sofa_icon*.png). Skipping .icns." >&2
    return 0
  fi
  if ! command -v sips >/dev/null 2>&1 || ! command -v iconutil >/dev/null 2>&1; then
    echo "[!] sips or iconutil not available; cannot generate .icns from PNG. Skipping." >&2
    return 0
  fi
  echo "[i] Generating .icns from: ${src_png}"
  local tmpdir
  tmpdir="$(mktemp -d)" || exit 1
  local iconset="${tmpdir}/AppIcon.iconset"
  mkdir -p "${iconset}"
  # Sizes (base and @2x)
  declare -a sizes=(16 32 128 256 512)
  for sz in "${sizes[@]}"; do
    sips -z "${sz}" "${sz}" "${src_png}" --out "${iconset}/icon_${sz}x${sz}.png" >/dev/null
    sips -z "$((sz*2))" "$((sz*2))" "${src_png}" --out "${iconset}/icon_${sz}x${sz}@2x.png" >/dev/null
  done
  # Also add 1024 for high-DPI
  sips -z 1024 1024 "${src_png}" --out "${iconset}/icon_512x512@2x.png" >/dev/null
  iconutil -c icns "${iconset}" -o "${out_icns}"
  rm -rf "${tmpdir}"
  if [[ -f "${out_icns}" ]]; then
    echo "[✓] Created .icns: ${out_icns}"
  else
    echo "[!] Failed to create .icns" >&2
  fi
}

ensure_icns

echo "[i] Building Sofa Jobs Navigator.app"
pyinstaller --noconfirm "packaging/macos/sjn_mac.spec"

APP_NAME="Sofa Jobs Navigator"
APP_PATH="dist/${APP_NAME}.app"

if [[ ! -d "${APP_PATH}" ]]; then
  echo "[!] Build failed: ${APP_PATH} not found" >&2
  exit 1
fi

DMG_PATH="dist/${APP_NAME}.dmg"
if command -v hdiutil >/dev/null 2>&1; then
  echo "[i] Creating DMG: ${DMG_PATH}"
  rm -f "${DMG_PATH}"
  hdiutil create -volname "${APP_NAME}" -srcfolder "${APP_PATH}" -ov -format UDZO "${DMG_PATH}" >/dev/null
else
  echo "[i] hdiutil not found; skipping DMG creation."
fi

echo "[✓] Build complete: ${APP_PATH}"
if [[ -f "${DMG_PATH}" ]]; then
  echo "[✓] DMG created: ${DMG_PATH}"
fi
