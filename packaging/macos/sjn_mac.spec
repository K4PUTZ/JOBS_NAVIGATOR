# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from pathlib import Path

base = Path(__file__).resolve().parents[2]  # Repo root containing "JOBS NAVIGATOR"
src = base / 'JOBS NAVIGATOR' / 'src'
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
    base / 'JOBS NAVIGATOR' / 'sofa_icon.png',
    base / 'JOBS NAVIGATOR' / 'sofa_icon_128.png',
    base / 'JOBS NAVIGATOR' / 'sofa_icon.ico',
    base / 'DRIVE_OPERATOR' / 'sofa_icon.png',
    base / 'DRIVE_OPERATOR' / 'sofa_icon_128.png',
    base / 'DRIVE_OPERATOR' / 'sofa_icon.ico',
    base / 'NAVIGATOR' / 'sofa_icon.ico',
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


a = Analysis(
    [str(src / 'sofa_jobs_navigator' / 'app.py')],
    pathex=[str(base)],
    binaries=[],
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
    exclude_binaries=True,
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
)
