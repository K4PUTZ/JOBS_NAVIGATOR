#!/usr/bin/env bash
# CI-friendly smoke test: runs with the embedded Python binary (if present)
# and executes the same small import test used locally. Exit code 0 == pass.
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_DIST="${ROOT_DIR}/dist/Sofa Jobs Navigator.app"
EMBED_PY="${APP_DIST}/Contents/Frameworks/Python.framework/Versions/3.11/bin/python3"
if [[ ! -x "${EMBED_PY}" ]]; then
  echo "[!] Embedded python not found: ${EMBED_PY}"
  exit 2
fi

"${EMBED_PY}" - <<'PY'
import importlib,sys
try:
    m=importlib.import_module('sofa_jobs_navigator.version')
    print('version', getattr(m,'VERSION','unknown'))
    # Quick import smoke for key deps
    import tkinter
    import platform
    print('tk', tkinter.Tk.__name__ if hasattr(tkinter,'Tk') else 'tk-not-found')
except Exception as e:
    print('error', e)
    raise
PY

echo '[✓] CI smoke test passed'
