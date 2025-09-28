#!/usr/bin/env bash
# Collect logs and minimal system info for support
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_DIST="${ROOT_DIR}/dist/Sofa Jobs Navigator.app"
OUT_DIR="${ROOT_DIR}/dist/support_report_$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "${OUT_DIR}"

echo "Collecting app logs and system info into ${OUT_DIR}"

if [[ -f "${APP_DIST}/Contents/Resources/sofa_jobs_navigator.log" ]]; then
  cp "${APP_DIST}/Contents/Resources/sofa_jobs_navigator.log" "${OUT_DIR}/" || true
fi

# Basic system info
uname -a > "${OUT_DIR}/system_uname.txt" || true
sw_vers > "${OUT_DIR}/sw_vers.txt" || true

# PyInstaller build metadata if available
if [[ -f "${ROOT_DIR}/dist/Sofa Jobs Navigator.app/Contents/Resources/PKG-INFO" ]]; then
  cp "${ROOT_DIR}/dist/Sofa Jobs Navigator.app/Contents/Resources/PKG-INFO" "${OUT_DIR}/" || true
fi

# List bundle contents (small snapshot)
ls -la "${APP_DIST}/Contents/Frameworks" > "${OUT_DIR}/frameworks_listing.txt" || true

# Zip up
ZIP_PATH="${OUT_DIR}.zip"
cd "${OUT_DIR}/.."
zip -r "${ZIP_PATH}" "$(basename "${OUT_DIR}")" >/dev/null || true

echo "Support report created: ${ZIP_PATH}"
