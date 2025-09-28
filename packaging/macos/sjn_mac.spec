# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from pathlib import Path

# Some PyInstaller execution contexts may not provide __file__ when running
# the spec; fall back to the current working directory to be robust.
if '__file__' in globals():
    spec_path = Path(__file__).resolve()
else:
    spec_path = Path.cwd().resolve()

# Walk upwards from the spec location and find the repository root by locating
# the directory that contains `src/sofa_jobs_navigator`. This is robust to
# different invocation CWDs and path layouts (spaces, mounts, etc.).
base = spec_path
found = None
for _ in range(6):
    candidate = base.resolve()
    if (candidate / 'src' / 'sofa_jobs_navigator').exists():
        found = candidate
        break
    if candidate.parent == candidate:
        break
    base = candidate.parent

# Determine the project root (the directory that contains the project folder
# with 'src/sofa_jobs_navigator'). This can be either the current 'base' or a
# parent that contains the 'JOBS NAVIGATOR' folder. Keep project_root as the
# directory that directly contains the project folder so other sibling
# packages (e.g., DRIVE_OPERATOR) are not automatically added to PYTHONPATH.
if found is None:
    # Best-effort fallback: go up 2 levels (legacy behavior)
    spec_root = spec_path.parents[2]
else:
    spec_root = found

# If spec_root already points to the project folder (it contains src/sofa_jobs_navigator),
# use it as project_root; otherwise look for a subfolder named 'JOBS NAVIGATOR'.
if (spec_root / 'src' / 'sofa_jobs_navigator').exists():
    project_root = spec_root
elif (spec_root / 'JOBS NAVIGATOR' / 'src' / 'sofa_jobs_navigator').exists():
    project_root = spec_root / 'JOBS NAVIGATOR'
else:
    raise RuntimeError("Could not locate project root containing src/sofa_jobs_navigator")

src = project_root / 'src'

# Only put the package's src directory into sys.path and into PyInstaller pathex
# so unrelated top-level folders (which may contain modules named 'logging')
# are not exposed and cannot shadow the stdlib.
sys.path.insert(0, str(src))

# Safe import of version metadata
try:
    from sofa_jobs_navigator.version import VERSION
except Exception:
    VERSION = "0.0.0"

app_name = 'Sofa Jobs Navigator'

# Collect data files (help images, readme, and iconset candidates)
datas = []

help_dir = src / 'sofa_jobs_navigator' / 'ui' / 'assets' / 'help'
if help_dir.exists():
    for p in help_dir.glob('*.png'):
        datas.append((str(p), 'sofa_jobs_navigator/ui/assets/help'))
    readme = help_dir / 'README.md'
    if readme.exists():
        datas.append((str(readme), 'sofa_jobs_navigator/ui/assets/help'))

icon_candidates = [
    project_root / 'sofa_icon.png',
    project_root / 'sofa_icon_128.png',
    project_root / 'sofa_icon.ico',
    project_root / 'DRIVE_OPERATOR' / 'sofa_icon.png',
    project_root / 'DRIVE_OPERATOR' / 'sofa_icon_128.png',
    project_root / 'DRIVE_OPERATOR' / 'sofa_icon.ico',
    project_root / 'NAVIGATOR' / 'sofa_icon.ico',
]
for p in icon_candidates:
    if p.exists():
        datas.append((str(p), '.'))

hiddenimports = [
    'googleapiclient.discovery',
    'googleapiclient.http',
    'googleapiclient._auth',
    'google.oauth2.credentials',
    'google.auth.transport.requests',
    'google_auth_oauthlib.flow',
    'httplib2',
]

block_cipher = None

# Attempt to locate the Python dynamic library and include it in the bundle.
# On macOS the bootloader will look for libpythonX.Y.dylib next to the
# executable; PyInstaller sometimes does not copy it automatically for
# conda/non-framework installs, so detect and add it explicitly.
import sysconfig
from pathlib import Path as _P

python_binaries = []
libname = f"libpython{sys.version_info.major}.{sys.version_info.minor}.dylib"
search_dirs = []
ldir = sysconfig.get_config_var('LIBDIR')
if ldir:
    search_dirs.append(_P(ldir))
exe_parent = _P(sys.executable).resolve().parents[1]
search_dirs.append(exe_parent / 'lib')
search_dirs.append(_P(sys.prefix) / 'lib')
search_dirs.append(_P(sys.base_prefix) / 'lib')
search_dirs.append(_P(sys.executable).resolve().parent)

found_lib = None
for d in search_dirs:
    try:
        candidate = (d / libname).resolve()
    except Exception:
        continue
    if candidate.exists():
        found_lib = candidate
        break

if found_lib:
    # Place the dylib into the bundle Frameworks directory. This makes the
    # library appear as Contents/Frameworks/<basename> where the bootloader
    # expects to find a Python runtime.
    python_binaries.append((str(found_lib), 'Frameworks'))
else:
    # No-op; PyInstaller may already include the runtime library for some envs
    pass



a = Analysis(
    [str(project_root / 'packaging' / 'macos' / '_sjn_entry.py')],
    pathex=[str(src)],
    binaries=python_binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[
        str(base / 'JOBS NAVIGATOR' / 'packaging' / 'macos' / 'hooks'),
        str(base / 'NAVIGATOR' / '__buildandrun'),  # legacy hook path (optional)
    ],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=False,
    name=app_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

icon_icns = None
for cand in [
    base / 'JOBS NAVIGATOR' / 'sofa_icon.icns',
    base / 'DRIVE_OPERATOR' / 'sofa_icon.icns',
    base / 'NAVIGATOR' / 'sofa_icon.icns',
]:
    if cand.exists():
        icon_icns = str(cand)
        break

app = BUNDLE(
    exe,
    name=f'{app_name}.app',
    icon=icon_icns,  # Use .icns if available; otherwise Tk sets icon at runtime
    bundle_identifier='com.sofa.jobsnavigator',
    info_plist={
        'CFBundleDisplayName': app_name,
        'CFBundleName': app_name,
        'CFBundleShortVersionString': VERSION,
        'CFBundleVersion': VERSION,
        'NSHighResolutionCapable': True,
    },
    # Ensure critical framework-level data is present. PyInstaller sometimes
    # places base_library.zip into the build directory instead of the final
    # Frameworks path; include base_library.zip and any runtime 'Python'
    # library explicitly via datas so they are available under
    # Contents/Frameworks when the bundle is created.
    datas=[
        # base_library.zip produced by Analysis; PyInstaller will resolve the
        # correct path at build time, but this hint keeps it present in the
        # final bundle.
        (str(Path('build') / ("sjn_mac") / 'base_library.zip'), 'Frameworks'),
    ],
)
