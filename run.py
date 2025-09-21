#!/usr/bin/env python3
# pyright: reportMissingImports=false, reportMissingModuleSource=false
"""
Convenience entry point to run the Sofa Jobs Navigator app from VS Code.

Usage:
- Open this file in VS Code and click the "Run Python File" play button.
- Or run from terminal: `python3 run.py`

This script ensures the local `src/` is on `sys.path` so imports work without installation.
"""

from __future__ import annotations

import faulthandler
import os
import argparse
import sys
from pathlib import Path

faulthandler.enable()

# Ensure local src is importable
ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

# Import and run the app
from sofa_jobs_navigator.app import run as app_run  # type: ignore  # noqa: E402
import tkinter as tk  # noqa: E402

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Sofa Jobs Navigator")
    parser.add_argument("--auto-quit-ms", type=int, default=None, help="Auto-quit the app after N milliseconds (testing)")
    return parser.parse_args()


def _maybe_auto_quit(root: tk.Tk, cli_ms: int | None) -> None:
    # Priority: CLI flag > env var
    env_ms = os.getenv("SJN_AUTO_QUIT_MS")
    try:
        env_val = int(env_ms) if env_ms is not None else None
    except ValueError:
        env_val = None
    delay = cli_ms if cli_ms is not None else env_val
    if delay and delay > 0:
        try:
            root.after(delay, lambda: root.quit())
        except Exception:
            pass


if __name__ == "__main__":
    args = _parse_args()
    # Monkey-patch tk.Tk to inject auto-quit scheduling after window creation
    _orig_tk = tk.Tk

    def _tk_factory(*a, **kw):
        r = _orig_tk(*a, **kw)
        _maybe_auto_quit(r, args.auto_quit_ms)
        return r

    tk.Tk = _tk_factory  # type: ignore[assignment]
    try:
        app_run()
    finally:
        tk.Tk = _orig_tk  # restore
