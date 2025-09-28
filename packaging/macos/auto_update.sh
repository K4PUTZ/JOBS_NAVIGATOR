#!/usr/bin/env bash
# Minimal auto-update helper.
# Usage: place this in the app Resources and let the app call it to check
# for updates. It downloads a DMG or ZIP from a URL and verifies SHA256 before
# replacing the installed app. This is intentionally minimal and requires the
# caller to prompt the user for consent.

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CACHE_DIR="${SCRIPT_DIR}/update_cache"
mkdir -p "${CACHE_DIR}"

# Inputs
REMOTE_URL="${1:-}"
REMOTE_SHA_URL="${2:-}"
TARGET_APP_DIR="${3:-/Applications}"
APP_NAME="Sofa Jobs Navigator"

if [[ -z "${REMOTE_URL}" || -z "${REMOTE_SHA_URL}" ]]; then
  echo "Usage: auto_update.sh <remote-dmg-or-zip-url> <remote-sha256-url> [target_install_dir]"
  exit 2
fi

TMPFILE="${CACHE_DIR}/download.tmp"
OUTFILE="${CACHE_DIR}/artifact"

echo "[i] Downloading artifact: ${REMOTE_URL}"
curl -L --fail -o "${TMPFILE}" "${REMOTE_URL}"

echo "[i] Downloading checksum: ${REMOTE_SHA_URL}"
curl -L --fail -o "${CACHE_DIR}/artifact.sha256" "${REMOTE_SHA_URL}"
EXPECTED_SHA=$(cat "${CACHE_DIR}/artifact.sha256" | awk '{print $1}')

echo "[i] Verifying SHA256"
shasum -a 256 "${TMPFILE}" | awk '{print $1}' | grep -x "${EXPECTED_SHA}" >/dev/null
if [[ $? -ne 0 ]]; then
  echo "[!] SHA256 verification failed. Aborting." >&2
  exit 3
fi

# Move the verified file to final name
mv "${TMPFILE}" "${OUTFILE}"

# If it's a DMG, mount and copy; if ZIP, unzip
if file "${OUTFILE}" | grep -q "dmg"; then
  MOUNT_DIR="${CACHE_DIR}/mnt"
  mkdir -p "${MOUNT_DIR}"
  hdiutil attach "${OUTFILE}" -mountpoint "${MOUNT_DIR}" -nobrowse -quiet
  cp -R "${MOUNT_DIR}/${APP_NAME}.app" "${TARGET_APP_DIR}/"
  hdiutil detach "${MOUNT_DIR}" -quiet
elif file "${OUTFILE}" | grep -q "Zip"; then
  unzip -q "${OUTFILE}" -d "${CACHE_DIR}/unpack"
  cp -R "${CACHE_DIR}/unpack/${APP_NAME}.app" "${TARGET_APP_DIR}/"
else
  echo "[!] Unknown artifact type; manual install required." >&2
  exit 4
fi

echo "[✓] Update installed to ${TARGET_APP_DIR}/${APP_NAME}.app"
