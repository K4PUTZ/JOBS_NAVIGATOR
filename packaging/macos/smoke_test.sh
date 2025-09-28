#!/usr/bin/env bash
# Quick headless smoke test: runs the embedded python to import the app and
# perform a small API call that does not require GUI.
set -euo pipefail
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# Candidate locations: packaging/dist and project root dist
APP_DIST_CAND1="${BASE_DIR}/dist/Sofa Jobs Navigator.app"
APP_DIST_CAND2="$(cd "${BASE_DIR}/.." && pwd)/dist/Sofa Jobs Navigator.app"
if [[ -d "${APP_DIST_CAND1}" ]]; then
  APP_DIST="${APP_DIST_CAND1}"
elif [[ -d "${APP_DIST_CAND2}" ]]; then
  APP_DIST="${APP_DIST_CAND2}"
else
  echo "[!] App not found in expected dist locations:
  ${APP_DIST_CAND1}
  ${APP_DIST_CAND2}"
  exit 2
fi

# Find embedded python binary dynamically (pick first matching version)
EMBED_PY="$(ls "${APP_DIST}/Contents/Frameworks/Python.framework/Versions"/*/bin/python3 2>/dev/null | head -n1 || true)"
if [[ -z "${EMBED_PY}" || ! -x "${EMBED_PY}" ]]; then
  echo "[!] Embedded python not found under ${APP_DIST}/Contents/Frameworks/Python.framework/Versions/*/bin/python3"
  exit 2
fi
# Run a tiny python snippet to import the package and print the version
"${EMBED_PY}" - <<'PY'
import importlib
try:
    mod = importlib.import_module('sofa_jobs_navigator.version')
    print('ok', getattr(mod, 'VERSION', 'unknown'))
except Exception as e:
    print('import-failed', e)
    raise
PY
