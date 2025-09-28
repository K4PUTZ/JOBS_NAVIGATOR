#!/usr/bin/env python3
"""
Prune an embedded Python.framework inside an .app bundle to reduce size.
This is conservative by default; run with --apply to actually delete files.

Usage:
  prune_framework.py --app "/path/to/Sofa Jobs Navigator.app" [--apply]

It will remove tests, tkinter tcl demo files, duplicated locales, .pyo/.pyc caches
and other non-essential files. Keep backups before running on release artifacts.
"""

import argparse
import os
import shutil
from pathlib import Path

PRUNE_PATTERNS = [
    'lib/python*/test',
    'lib/python*/tests',
    'lib/python*/site-packages/*-info',
    'lib/python*/site-packages/test',
    'lib/python*/site-packages/tests',
    'lib/python*/site-packages/*.dist-info',
    'lib/python*/site-packages/*.egg-info',
    'lib/python*/ensurepip',
    'lib/python*/idlelib',
    'lib/python*/lib2to3',
    'lib/python*/tkinter/test',
    'lib/python*/tkinter/demo',
    'lib/python*/site-packages/pip',
]

EXTRA_FILES = [
    'Resources/English.lproj/Documentation',
]


def find_matches(root: Path, pattern: str):
    # glob supports patterns like 'lib/python*/test'
    return list(root.glob(pattern))


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--app', required=True)
    p.add_argument('--apply', action='store_true')
    args = p.parse_args()

    app = Path(args.app)
    if not app.exists():
        print(f"[!] App not found: {app}")
        return 2

    framework = app / 'Contents' / 'Frameworks' / 'Python.framework'
    if not framework.exists():
        print(f"[!] Python.framework not found inside {app}")
        return 2

    print(f"[i] Prune target: {framework}")

    candidates = []
    for pat in PRUNE_PATTERNS:
        matches = find_matches(framework, pat)
        for m in matches:
            candidates.append(m)

    for extra in EXTRA_FILES:
        e = framework.parent.parent / extra
        if e.exists():
            candidates.append(e)

    if not candidates:
        print('[i] No prune candidates found.')
        return 0

    print('[i] Prune candidates:')
    for c in candidates:
        print(' -', c)

    if not args.apply:
        print('\n[i] Dry run complete. Rerun with --apply to remove these files.')
        return 0

    # Apply deletions
    for c in candidates:
        try:
            if c.is_dir():
                shutil.rmtree(c)
            else:
                c.unlink()
            print(f"[+] Removed {c}")
        except Exception as e:
            print(f"[!] Failed to remove {c}: {e}")

    print('[✓] Prune applied')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
