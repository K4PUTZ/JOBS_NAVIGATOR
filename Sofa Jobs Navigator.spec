# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['packaging/macos/_sjn_entry.py'],
    pathex=['/Volumes/Expansion/----- PESSOAL -----/PYTHON/JOBS NAVIGATOR/packaging/macos/../../../JOBS NAVIGATOR/src'],
    binaries=[('/Library/Frameworks/Python.framework/Versions/3.11/Python', '_internal/Python')],
    datas=[('/Volumes/Expansion/----- PESSOAL -----/PYTHON/JOBS NAVIGATOR/packaging/macos/../../../JOBS NAVIGATOR/sofa_icon.icns', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Sofa Jobs Navigator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Sofa Jobs Navigator',
)
