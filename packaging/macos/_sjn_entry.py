"""Small launcher used by the PyInstaller spec.

This file imports the real package entrypoint so PyInstaller's script
directory doesn't expose `src/sofa_jobs_navigator` as a top-level path
which could shadow stdlib modules like `logging`.
"""
from __future__ import annotations

import os
import sys

# When running as a frozen onedir build, add the onedir root and _internal
# site-packages to sys.path so pure-Python packages copied into the build
# (for debugging) are importable by the frozen importer.
if getattr(sys, 'frozen', False):
    # dirname of the executable is the onedir root for this layout
    exe_dir = os.path.dirname(sys.executable)
    candidate_site = os.path.join(exe_dir, '_internal', 'site-packages')
    if os.path.isdir(candidate_site) and candidate_site not in sys.path:
        sys.path.insert(0, candidate_site)
    # also allow packages placed next to the executable
    if exe_dir not in sys.path:
        sys.path.insert(0, exe_dir)
    # If running inside a macOS .app bundle, ensure the bundle's Frameworks
    # contains the lib-dynload directory and base_library.zip are on sys.path.
    # This helps the frozen interpreter find compiled extensions and the stdlib
    # when the bundle was manually assembled.
    # Example exe path: /.../Sofa Jobs Navigator.app/Contents/MacOS/Sofa Jobs Navigator
    if '.app/Contents/MacOS' in exe_dir:
        bundle_root = exe_dir.split('.app/Contents/MacOS')[0] + '.app/Contents'
        fw_root = os.path.join(bundle_root, 'Frameworks')
        dynload = os.path.join(fw_root, 'python3.11', 'lib-dynload')
        base_zip = os.path.join(fw_root, 'base_library.zip')
        if os.path.isdir(dynload) and dynload not in sys.path:
            sys.path.insert(0, dynload)
        if os.path.isfile(base_zip) and base_zip not in sys.path:
            sys.path.insert(0, base_zip)

from sofa_jobs_navigator.app import run


if __name__ == '__main__':
    run()
