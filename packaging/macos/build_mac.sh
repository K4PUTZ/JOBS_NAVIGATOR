#!/usr/bin/env bash
set -euo pipefail

# Build macOS .app bundle for Sofa Jobs Navigator using PyInstaller
# Produces: dist/Sofa Jobs Navigator.app and optional DMG if hdiutil is available.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="${SCRIPT_DIR}/../../.."
APP_DIR="${ROOT_DIR}/JOBS NAVIGATOR"

cd "${APP_DIR}"

# Prefer a venv inside the project if available to ensure PyInstaller and the
# Python runtime used for bundling match the expected stdlib. Fall back to
# system python3 if no venv is found.
# Decide which Python to use for building. Prefer an explicit env variable
# SJN_PYTHON (set by CI or user). Otherwise, try common system Python locations
# and prefer /usr/local (Homebrew) then /usr/bin. We will create a temporary
# clean venv under .venv_build and use it for PyInstaller to ensure a stable
# macOS runtime layout (avoid Conda-managed Python runtimes).
if [[ -n "${SJN_PYTHON:-}" ]]; then
  SYSTEM_PYTHON="${SJN_PYTHON}"
else
  # Common candidates
  for p in "/usr/local/bin/python3" "/opt/homebrew/bin/python3" "/usr/bin/python3"; do
    if [[ -x "${p}" ]]; then
      SYSTEM_PYTHON="${p}"
      break
    fi
  done
fi

if [[ -z "${SYSTEM_PYTHON:-}" ]]; then
  echo "[!] No suitable system Python found. Set SJN_PYTHON to a python3 executable." >&2
  exit 1
fi

BUILD_VENV="${APP_DIR}/.venv_build"
if [[ -d "${BUILD_VENV}" ]]; then
  echo "[i] Reusing existing build venv: ${BUILD_VENV}"
else
  echo "[i] Creating build venv at ${BUILD_VENV} using ${SYSTEM_PYTHON}"
  "${SYSTEM_PYTHON}" -m venv "${BUILD_VENV}"
fi

PYTHON_EXEC="${BUILD_VENV}/bin/python"

echo "[i] Using build python: ${PYTHON_EXEC}"

if ! "${PYTHON_EXEC}" -m pip show pyinstaller >/dev/null 2>&1; then
  echo "[i] Installing pyinstaller into build venv..."
  "${PYTHON_EXEC}" -m pip install --upgrade pip
  "${PYTHON_EXEC}" -m pip install pyinstaller
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

echo "[i] Building Sofa Jobs Navigator.app using ${PYTHON_EXEC} (onedir mode, clean entry-script build)"
# When building with a .spec file, some makespec options like --onedir are
# not accepted. Build directly from the small entry script in onedir mode
# to get a stable layout suitable for macOS bundles.
ENTRY_SCRIPT="packaging/macos/_sjn_entry.py"
# Try to locate the system Python shared library; if found, instruct
# PyInstaller to add it into the _internal folder so the bootloader can
# load it at runtime (destination _internal/Python).
PY_SHARED=""
PY_BUILD_VER="$("${PYTHON_EXEC}" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
if [[ -f "/Library/Frameworks/Python.framework/Versions/${PY_BUILD_VER}/Python" ]]; then
  PY_SHARED="/Library/Frameworks/Python.framework/Versions/${PY_BUILD_VER}/Python"
fi

PYI_CMD=("${PYTHON_EXEC}" -m PyInstaller --noconfirm --onedir --clean)
PYI_CMD+=(--name "Sofa Jobs Navigator")
PYI_CMD+=(--add-data "${APP_DIR}/sofa_icon.icns:.")
PYI_CMD+=(--paths "${APP_DIR}/src")
if [[ -n "${PY_SHARED}" ]]; then
  echo "[i] Adding Python shared lib to PyInstaller build: ${PY_SHARED} -> _internal/Python"
  PYI_CMD+=(--add-binary "${PY_SHARED}:_internal/Python")
fi
PYI_CMD+=("${ENTRY_SCRIPT}")

"${PYI_CMD[@]}"

APP_NAME="Sofa Jobs Navigator"
APP_PATH="dist/${APP_NAME}.app"

if [[ ! -d "${APP_PATH}" ]]; then
  echo "[!] Build failed: ${APP_PATH} not found" >&2
  exit 1
fi

DMG_PATH="dist/${APP_NAME}.dmg"
if command -v hdiutil >/dev/null 2>&1; then
  echo "[i] Creating user-friendly DMG: ${DMG_PATH} (with Applications link and install instructions)"
  rm -f "${DMG_PATH}"
  # Prepare a temporary staging dir with the .app and an Applications symlink
  DMG_STAGING="$(mktemp -d)"
  trap 'rm -rf "${DMG_STAGING}"' EXIT
  mkdir -p "${DMG_STAGING}"
  echo "[i] Staging app into ${DMG_STAGING}"
  cp -R "${APP_PATH}" "${DMG_STAGING}/"
  # Create an Applications symlink for drag-and-drop UX
  ln -s /Applications "${DMG_STAGING}/Applications"
  # Add a short install instructions file into the staging area
  cat > "${DMG_STAGING}/INSTALL.txt" <<'INSTALL_EOF'
Drag the 'Sofa Jobs Navigator.app' into the Applications folder alias on the right.
If macOS blocks execution, Control-click (right-click) the app and choose Open to allow it.
Logs: the app writes a log at Contents/Resources/sofa_jobs_navigator.log inside the .app bundle.
INSTALL_EOF
  # Create the compressed DMG from the staging folder for a nicer UX
  hdiutil create -volname "${APP_NAME}" -srcfolder "${DMG_STAGING}" -ov -format UDZO "${DMG_PATH}" >/dev/null
  # Compute a SHA256 checksum for the DMG to provide integrity verification
  if command -v shasum >/dev/null 2>&1; then
    echo "[i] Generating SHA256 checksum for ${DMG_PATH}"
    mkdir -p dist
    shasum -a 256 "${DMG_PATH}" > "dist/${APP_NAME}.dmg.sha256"
    echo "[i] Checksum written to dist/${APP_NAME}.dmg.sha256"
  fi
else
  echo "[i] hdiutil not found; skipping DMG creation."
fi

echo "[✓] Build complete: ${APP_PATH}"
if [[ -f "${DMG_PATH}" ]]; then
  echo "[✓] DMG created: ${DMG_PATH}"
fi

# Post-build fixes for macOS runtime layout
# Some Python installs and PyInstaller runs may not place the Python
# shared library or base_library.zip at the exact locations the frozen
# bootloader expects. Perform best-effort copies and ad-hoc codesigning
# so the produced bundle is runnable for local QA.
PY_LIB_SRC="$(python3 -c 'import sysconfig,sys; import pathlib as p; ld=sysconfig.get_config_var("LIBDIR"); print(ld or "")')"
if [[ -n "${PY_LIB_SRC}" ]]; then
  # Look for a likely Python shared library (.dylib or 'Python') under the
  # system framework. Prefer the framework executable used earlier by
  # PyInstaller (if present).
  CAND_PYLIB="${PY_LIB_SRC}/libpython${PY_BUILD_VER}.dylib"
  if [[ -f "${CAND_PYLIB}" ]]; then
    echo "[i] Copying Python shared lib into bundle Frameworks"
    mkdir -p "${APP_PATH}/Contents/Frameworks"
    cp "${CAND_PYLIB}" "${APP_PATH}/Contents/Frameworks/Python" || true
  fi
fi

# If base_library.zip exists in the build output, ensure it is present in the
# final bundle under Contents/Frameworks/base_library.zip
BUILD_BASE_ZIP="${APP_DIR}/build/sjn_mac/base_library.zip"
if [[ -f "${BUILD_BASE_ZIP}" ]]; then
  echo "[i] Ensuring base_library.zip is present in bundle Frameworks"
  mkdir -p "${APP_PATH}/Contents/Frameworks"
  cp -f "${BUILD_BASE_ZIP}" "${APP_PATH}/Contents/Frameworks/base_library.zip"
fi

# Ad-hoc codesign the copied Python runtime so macOS will allow the loader
# to open it during local testing. This uses ad-hoc signing (no Developer ID).
if [[ -f "${APP_PATH}/Contents/Frameworks/Python" ]]; then
  echo "[i] Codesigning embedded Python runtime (ad-hoc)"
  codesign --sign - --force "${APP_PATH}/Contents/Frameworks/Python" || true
  # Also re-sign the app executable to keep signatures consistent
  codesign --sign - --force "${APP_PATH}/Contents/MacOS/${APP_NAME}" || true
fi

# Manual assembly: ensure the app bundle contains the expected onedir runtime
# layout (copy bootloader from build, base_library, localpycs and lib-dynload).
BUILD_DIR="${APP_DIR}/build/Sofa Jobs Navigator"
BOOTLOADER_SRC="${BUILD_DIR}/Sofa Jobs Navigator"
# Determine where the system Python.framework (used for build) is located.
# Try common locations: /Library/Frameworks, /usr/local/Frameworks, /opt/homebrew/Frameworks
PY_VER="${PY_BUILD_VER}"
PY_FRAMEWORK_SRC=""
for root in "/Library/Frameworks" "/usr/local/Frameworks" "/opt/homebrew/Frameworks"; do
  candidate="${root}/Python.framework/Versions/${PY_VER}"
  if [[ -d "${candidate}" ]]; then
    PY_FRAMEWORK_SRC="${candidate}"
    PY_FRAMEWORK_ROOT="${root}/Python.framework"
    break
  fi
done
if [[ -z "${PY_FRAMEWORK_SRC}" ]]; then
  echo "[!] Could not locate Python.framework Versions/${PY_VER} under common locations. Falling back to /Library/Frameworks path." >&2
  PY_FRAMEWORK_SRC="/Library/Frameworks/Python.framework/Versions/${PY_VER}"
  PY_FRAMEWORK_ROOT="/Library/Frameworks/Python.framework"
fi
echo "[i] Using PY_FRAMEWORK_SRC=${PY_FRAMEWORK_SRC} (root=${PY_FRAMEWORK_ROOT})"

echo "[i] Performing manual assembly of .app from onedir build"
mkdir -p "${APP_PATH}/Contents/MacOS"
mkdir -p "${APP_PATH}/Contents/Frameworks"

if [[ -f "${BOOTLOADER_SRC}" ]]; then
  echo "[i] Installing bootloader into app Frameworks and creating launcher wrapper"
  # Place the real bootloader inside Contents/Frameworks so we can use a small
  # launcher wrapper in Contents/MacOS that configures environment variables
  # (PYTHONHOME, PYTHONPATH) and then execs the real bootloader. This avoids
  # relying on PyInstaller's internal extraction paths and stabilizes double-
  # click behavior on macOS.
  BOOT_REAL="${APP_PATH}/Contents/Frameworks/_sjn_bootloader_real"
  cp -f "${BOOTLOADER_SRC}" "${BOOT_REAL}"
  chmod +x "${BOOT_REAL}" || true

  # Create a small shell-based launcher at Contents/MacOS/Sofa Jobs Navigator
  LAUNCHER_PATH="${APP_PATH}/Contents/MacOS/Sofa Jobs Navigator"
  cat > "${LAUNCHER_PATH}" <<'LAUNCHER_EOF'
#!/usr/bin/env bash
set -euo pipefail
# Resolve path to this executable and the app Contents dir
APP_EXEC="$0"
# dirname(APP_EXEC) -> .../Sofa Jobs Navigator.app/Contents/MacOS
APP_CONTENTS_DIR="$(cd "$(dirname "${APP_EXEC}")/.." && pwd)"
FRAMEWORKS_DIR="${APP_CONTENTS_DIR}/Frameworks"
# Where the real bootloader binary was installed
BOOT_REAL="${FRAMEWORKS_DIR}/_sjn_bootloader_real"

# Export environment so the embedded runtime can be found reliably
export PYTHONHOME="${FRAMEWORKS_DIR}"
# Ensure frozen archive and localpycs are on sys.path
export PYTHONPATH="${FRAMEWORKS_DIR}/base_library.zip:${FRAMEWORKS_DIR}/localpycs:${PYTHONPATH:-}"
export PYTHONDONTWRITEBYTECODE=1

# Change to Resources (common place for app assets) so relative paths resolve
cd "${APP_CONTENTS_DIR}/Resources" || true

# Exec the real bootloader with all args
exec "${BOOT_REAL}" "$@"
LAUNCHER_EOF

  chmod +x "${LAUNCHER_PATH}" || true
fi

# Copy project source into Resources/app_src so launcher can fallback to running
# the app using system python if the frozen bootloader cannot load the
# embedded runtime. This makes the bundle usable for local QA on machines
# that have a reasonably recent python3 + tkinter available.
echo "[i] Copying project source into app Resources for fallback execution"
mkdir -p "${APP_PATH}/Contents/Resources/app_src"
rsync -a --exclude 'build' --exclude '.venv_build' --exclude '.git' "${APP_DIR}/src/" "${APP_PATH}/Contents/Resources/app_src/" || true

cat > "${LAUNCHER_PATH}" <<'LAUNCHER_EOF'
#!/usr/bin/env bash
set -euo pipefail
APP_EXEC="$0"
# path to the bundle Contents dir
APP_CONTENTS_DIR="$(cd "$(dirname "${APP_EXEC}")/.." && pwd)"
FRAMEWORKS_DIR="${APP_CONTENTS_DIR}/Frameworks"
BOOT_REAL="${FRAMEWORKS_DIR}/_sjn_bootloader_real"

# Prepare environment variables used by embedded interpreter
export PYTHONDONTWRITEBYTECODE=1

# 1) Prefer running the embedded Python interpreter directly (bypasses
#    PyInstaller bootloader). This will work if the build copied a Python
#    binary into Contents/Frameworks/Python and included base_library.zip and
#    localpycs.
EMBED_PY_BIN="${FRAMEWORKS_DIR}/Python"
if [[ -x "${EMBED_PY_BIN}" ]]; then
  export PYTHONHOME="${FRAMEWORKS_DIR}"
  export PYTHONPATH="${FRAMEWORKS_DIR}/base_library.zip:${FRAMEWORKS_DIR}/localpycs:${PYTHONPATH:-}"
  echo "[i] Running embedded Python interpreter: ${EMBED_PY_BIN}"
  cd "${APP_CONTENTS_DIR}/Resources" || true
  exec "${EMBED_PY_BIN}" -m sofa_jobs_navigator.app "$@"
fi

# 2) If no embedded interpreter, attempt to run the PyInstaller bootloader
if [[ -x "${BOOT_REAL}" ]]; then
  echo "[i] Trying relocated PyInstaller bootloader: ${BOOT_REAL}"
  # run as child; if it exits successfully we stop, otherwise continue
  "${BOOT_REAL}" "$@" && exit 0 || true
fi

# 3) Fallback to system python3 using the copied source in Resources/app_src
FALLBACK_PYTHON="$(command -v python3 || true)"
if [[ -n "${FALLBACK_PYTHON}" ]]; then
  echo "[i] Falling back to system python: ${FALLBACK_PYTHON}"
  APP_SRC_DIR="${APP_CONTENTS_DIR}/Resources/app_src"
  export PYTHONPATH="${APP_SRC_DIR}:${PYTHONPATH:-}"
  cd "${APP_CONTENTS_DIR}/Resources" || true
  exec "${FALLBACK_PYTHON}" -m sofa_jobs_navigator.app "$@"
fi

echo "[!] No available interpreter (embedded, bootloader, or system python3) to run the app."
exit 2
LAUNCHER_EOF

chmod +x "${LAUNCHER_PATH}" || true

if [[ -f "${BUILD_DIR}/base_library.zip" ]]; then
  echo "[i] Copying base_library.zip into app Frameworks"
  cp -f "${BUILD_DIR}/base_library.zip" "${APP_PATH}/Contents/Frameworks/base_library.zip"
fi

if [[ -d "${BUILD_DIR}/localpycs" ]]; then
  echo "[i] Copying localpycs into app Frameworks"
  rm -rf "${APP_PATH}/Contents/Frameworks/localpycs"
  cp -R "${BUILD_DIR}/localpycs" "${APP_PATH}/Contents/Frameworks/"
fi

# Copy lib-dynload from system Python so compiled extension modules are
# available under Contents/Frameworks/pythonX.Y/lib-dynload
if [[ -d "${PY_FRAMEWORK_SRC}/lib/python${PY_VER}/lib-dynload" ]]; then
  PY_DYNLOAD_SRC="${PY_FRAMEWORK_SRC}/lib/python${PY_VER}/lib-dynload"
  PY_DYNLOAD_DEST="${APP_PATH}/Contents/Frameworks/python${PY_VER}/lib-dynload"
  echo "[i] Copying lib-dynload into app Frameworks: ${PY_DYNLOAD_SRC} -> ${PY_DYNLOAD_DEST}"
  mkdir -p "${PY_DYNLOAD_DEST}"
  cp -R "${PY_DYNLOAD_SRC}"/* "${PY_DYNLOAD_DEST}/" || true
fi

# Copy Python shared library into Contents/Frameworks/Python if missing
SYS_PY_LIB="${PY_FRAMEWORK_SRC}/Python"
if [[ -f "${SYS_PY_LIB}" && ! -f "${APP_PATH}/Contents/Frameworks/Python" ]]; then
  echo "[i] Copying system Python into bundle Frameworks"
  cp -f "${SYS_PY_LIB}" "${APP_PATH}/Contents/Frameworks/Python"
  chmod +x "${APP_PATH}/Contents/Frameworks/Python" || true
fi

# Ensure PyInstaller expected _internal/Python path exists. Copy the
# Python shared library into _internal/Python (real file) so the bootloader
# can dlopen it reliably (symlinks sometimes fail under code-signing/dyld).
echo "[i] Creating ${APP_PATH}/Contents/Frameworks/_internal and copying Python shared lib"
mkdir -p "${APP_PATH}/Contents/Frameworks/_internal"
PY_SHARED_SRC="${PY_FRAMEWORK_SRC}/Python"
if [[ -f "${PY_SHARED_SRC}" ]]; then
  PY_INTERNAL_DEST="${APP_PATH}/Contents/Frameworks/_internal/Python"
  echo "[i] Copying Python shared library: ${PY_SHARED_SRC} -> ${PY_INTERNAL_DEST}"
  cp -f "${PY_SHARED_SRC}" "${PY_INTERNAL_DEST}" || true
  chmod +x "${PY_INTERNAL_DEST}" || true
  # Set a stable install_name so dyld can find it via @rpath
  echo "[i] Setting install_name of embedded Python to @rpath/Python"
  install_name_tool -id "@rpath/Python" "${PY_INTERNAL_DEST}" || true
  # Add an rpath to the app executable so @rpath resolves to ../Frameworks
  EXE_PATH="${APP_PATH}/Contents/MacOS/${APP_NAME}"
  if [[ -f "${EXE_PATH}" ]]; then
    echo "[i] Adding rpath @executable_path/../Frameworks to executable"
    install_name_tool -add_rpath "@executable_path/../Frameworks" "${EXE_PATH}" || true
  fi
  # Codesign the copied shared library and the executable for local testing
  echo "[i] Codesigning embedded _internal/Python and executable (ad-hoc)"
  codesign --sign - --force "${PY_INTERNAL_DEST}" || true
  if [[ -f "${EXE_PATH}" ]]; then
    codesign --sign - --force "${EXE_PATH}" || true
  fi
fi

# === New: embed a copy of the full Python.framework into the .app so the
# application can be fully self-contained. This copies the system Python
# framework (used by the build) into Contents/Frameworks/Python.framework
# and installs the project into that embedded Python's site-packages.
EMBED_FRAMEWORK_DEST="${APP_PATH}/Contents/Frameworks/Python.framework"
  if [[ -d "${PY_FRAMEWORK_SRC}" ]]; then
  echo "[i] Embedding full Python.framework into app: ${EMBED_FRAMEWORK_DEST}"
  # Remove existing embedded framework to ensure a clean copy
  rm -rf "${EMBED_FRAMEWORK_DEST}"
  echo "[i] Copying Python.framework from ${PY_FRAMEWORK_ROOT} to ${EMBED_FRAMEWORK_DEST}"
  cp -R "${PY_FRAMEWORK_ROOT}" "${APP_PATH}/Contents/Frameworks/" || {
    echo "[!] Failed to copy Python.framework from ${PY_FRAMEWORK_ROOT} to app bundle. Check permissions." >&2
  }
  # Make sure the embedded python binary exists and is executable
  EMBED_PY_BIN="${EMBED_FRAMEWORK_DEST}/Versions/${PY_VER}/bin/python3"
  if [[ -x "${EMBED_PY_BIN}" ]]; then
    echo "[i] Embedded python binary: ${EMBED_PY_BIN}"
    # Upgrade pip and install the project into embedded site-packages (no deps)
    echo "[i] Installing project into embedded Python site-packages (no-deps)"
    "${EMBED_PY_BIN}" -m ensurepip --upgrade || true
    "${EMBED_PY_BIN}" -m pip install --upgrade pip setuptools wheel || true
    echo "[i] Installing project and dependencies into embedded Python (this may take a moment)";
    # Install the project including its dependencies so embedded runtime is self-contained
    if ! "${EMBED_PY_BIN}" -m pip install "${APP_DIR}"; then
      echo "[!] pip install into embedded Python failed. Attempting to install from requirements.txt if present." >&2
      if [[ -f "${APP_DIR}/requirements.txt" ]]; then
        "${EMBED_PY_BIN}" -m pip install -r "${APP_DIR}/requirements.txt" || true
      fi
    fi
    # List a few installed packages for debugging
    "${EMBED_PY_BIN}" -m pip freeze | sed -n '1,120p' || true
  else
    echo "[!] Embedded Python binary not found or not executable: ${EMBED_PY_BIN}" >&2
    echo "[i] Listing ${EMBED_FRAMEWORK_DEST} contents for debugging:"
    ls -la "${EMBED_FRAMEWORK_DEST}" || true
    ls -la "${EMBED_FRAMEWORK_DEST}/Versions" || true
  fi
fi

# Codesign runtime pieces for local testing
if [[ -f "${APP_PATH}/Contents/Frameworks/Python" ]]; then
  echo "[i] Codesigning embedded Python (ad-hoc)"
  codesign --sign - --force "${APP_PATH}/Contents/Frameworks/Python" || true
fi
if [[ -f "${APP_PATH}/Contents/MacOS/Sofa Jobs Navigator" ]]; then
  echo "[i] Codesigning app executable (ad-hoc)"
  codesign --sign - --force "${APP_PATH}/Contents/MacOS/Sofa Jobs Navigator" || true
fi

# Replace launcher to run the embedded framework python directly (self-contained)
LAUNCHER_PATH="${APP_PATH}/Contents/MacOS/Sofa Jobs Navigator"
cat > "${LAUNCHER_PATH}" <<'LAUNCHER_EOF'
#!/usr/bin/env bash
set -euo pipefail
APP_EXEC="$0"
APP_CONTENTS_DIR="$(cd "$(dirname "${APP_EXEC}")/.." && pwd)"
# path to the log file inside the app bundle Resources (helpful for support)
LOG_FILE="${APP_CONTENTS_DIR}/Resources/sofa_jobs_navigator.log"
mkdir -p "$(dirname "${LOG_FILE}")"
# Redirect stdout/stderr to a rotating log (append) and also to the console
exec >>"${LOG_FILE}" 2>&1
echo "--- Sofa Jobs Navigator start: $(date -u +%Y-%m-%dT%H:%M:%SZ) ---"

# Embedded framework python
EMBED_PY="${APP_CONTENTS_DIR}/Frameworks/Python.framework/Versions/3.11/bin/python3"
if [[ -x "${EMBED_PY}" ]]; then
  export PYTHONDONTWRITEBYTECODE=1
  # Ensure the embedded python can find installed packages
  export PYTHONPATH="${APP_CONTENTS_DIR}/Resources/app_src:${PYTHONPATH:-}"
  cd "${APP_CONTENTS_DIR}/Resources" || true
  echo "[i] Running embedded Python interpreter: ${EMBED_PY}"
  echo "[i] PYTHONPATH=${PYTHONPATH}"
  exec "${EMBED_PY}" -m sofa_jobs_navigator.app "$@"
fi

echo "[!] Embedded python not found: ${EMBED_PY}. Falling back to system python3 if available."
SYS_PY="$(command -v python3 || true)"
if [[ -n "${SYS_PY}" ]]; then
  echo "[i] Falling back to system python: ${SYS_PY}"
  APP_SRC_DIR="${APP_CONTENTS_DIR}/Resources/app_src"
  export PYTHONPATH="${APP_SRC_DIR}:${PYTHONPATH:-}"
  cd "${APP_CONTENTS_DIR}/Resources" || true
  exec "${SYS_PY}" -m sofa_jobs_navigator.app "$@"
fi

echo "[!] No python available to run the app."
exit 2
LAUNCHER_EOF

chmod +x "${LAUNCHER_PATH}" || true
codesign --sign - --force "${LAUNCHER_PATH}" || true

# Developer ID signing and notarization placeholders
if [[ -n "${SJN_DEVID_CERT:-}" ]]; then
  echo "[i] Developer ID certificate provided: ${SJN_DEVID_CERT}. Performing official codesign (this may replace ad-hoc signatures)"
  # Recommended codesign flags for Developer ID distribution
  codesign --sign "${SJN_DEVID_CERT}" --timestamp --options runtime --deep --force "${APP_PATH}" || true
  # Notarization (optional) - requires xcrun notarytool and credentials. Provide
  # SJN_NOTARY_API_KEY_PATH (path to AuthKey_*.p8), SJN_NOTARY_ISSUER (Issuer ID) and
  # optionally SJN_NOTARY_KEY_ID if needed by your setup.
  if [[ -n "${SJN_NOTARY_API_KEY_PATH:-}" && -n "${SJN_NOTARY_ISSUER:-}" ]]; then
    if command -v xcrun >/dev/null 2>&1; then
      echo "[i] Submitting artifact for notarization using notarytool (this may take a while)"
      if [[ -f "${DMG_PATH:-}" ]]; then
        xcrun notarytool submit "${DMG_PATH}" --key "${SJN_NOTARY_API_KEY_PATH}" --issuer "${SJN_NOTARY_ISSUER}" --wait || true
        xcrun stapler staple "${DMG_PATH}" || true
      else
        echo "[i] No DMG found to notarize; notarize the app bundle directly if you prefer." 
      fi
    else
      echo "[!] xcrun not found; cannot run notarytool. Skipping notarization." >&2
    fi
  else
    echo "[i] Notarization variables (SJN_NOTARY_API_KEY_PATH, SJN_NOTARY_ISSUER) not set; skipping notarization." 
  fi
else
  echo "[i] No Developer ID cert (SJN_DEVID_CERT) provided. App is ad-hoc signed for local QA only. To enable official signing, set SJN_DEVID_CERT and SJN_NOTARY_* env vars." 
fi

# Optional: run framework pruning to reduce embedded Python.framework size
if [[ "${SJN_PRUNE:-0}" != "0" ]]; then
  if command -v python3 >/dev/null 2>&1; then
    echo "[i] Running framework prune tool (will apply deletions). Pass SJN_PRUNE=1 to enable." 
    python3 "${SCRIPT_DIR}/prune_framework.py" --app "${APP_PATH}" --apply || true
  else
    echo "[!] python3 not found; skipping framework prune." >&2
  fi
fi

echo "[✓] Manual assembly complete: ${APP_PATH}"
