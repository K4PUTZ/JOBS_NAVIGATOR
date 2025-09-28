#!/usr/bin/env python3
"""Sync package version in pyproject.toml from the package `VERSION` constant.

Usage:
  python tools/sync_version.py        # updates pyproject.toml in-place
  python tools/sync_version.py --dry  # print the discovered version but do not write

This avoids importing the package during builds and keeps a single source
of truth in `src/sofa_jobs_navigator/version.py`.
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
PACKAGE_VERSION_PY = ROOT / "src" / "sofa_jobs_navigator" / "version.py"
PYPROJECT = ROOT / "pyproject.toml"


def discover_version(path: pathlib.Path) -> str:
    text = path.read_text(encoding="utf8")
    # Accept optional type annotations like: VERSION: str = "1.3.7"
    m = re.search(r"^VERSION(?:\s*:\s*[^=]+)?\s*=\s*[\"']([^\"']+)[\"']", text, flags=re.M)
    if not m:
        raise SystemExit(f"Couldn't find VERSION in {path}")
    return m.group(1)


def update_pyproject(pyproject: pathlib.Path, version: str) -> bool:
    text = pyproject.read_text(encoding="utf8")
    # replace the first top-level 'version = "..."' occurrence
    new_text, n = re.subn(r'^(version\s*=\s*)["\'][^"\']+["\']',
                         lambda m: f'{m.group(1)}"{version}"',
                         text,
                         count=1,
                         flags=re.M)
    if n == 0:
        raise SystemExit(f"No 'version = ...' line found in {pyproject}")
    if new_text == text:
        return False
    pyproject.write_text(new_text, encoding="utf8")
    return True


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Sync pyproject.toml version from package VERSION")
    ap.add_argument("--dry", action="store_true", help="discover and print the version but don't write")
    args = ap.parse_args(argv)

    version = discover_version(PACKAGE_VERSION_PY)
    print(f"Discovered version: {version}")
    if args.dry:
        return 0

    changed = update_pyproject(PYPROJECT, version)
    if changed:
        print(f"Updated {PYPROJECT} -> version = \"{version}\"")
    else:
        print(f"{PYPROJECT} already at version {version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
