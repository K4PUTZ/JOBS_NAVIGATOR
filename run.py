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

# Import only the lightweight version helper early so `--version` works
from sofa_jobs_navigator.version import app_display_title  # noqa: E402
from sofa_jobs_navigator.maintenance.factory_reset import perform_factory_reset  # noqa: E402

import tkinter as tk  # noqa: E402

# Defer importing the app module until after we install the tkinter monkey-patch

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Sofa Jobs Navigator")
    parser.add_argument("--auto-quit-ms", type=int, default=None, help="Auto-quit the app after N milliseconds (testing)")
    parser.add_argument("-V", "--version", action="store_true", help="Print version and exit")
    parser.add_argument("--factory-reset", action="store_true", help="Reset user config, tokens and logs before launch")
    return parser.parse_args()


def _maybe_auto_quit(root: tk.Tk, cli_ms: int | None) -> None:
    """Optionally schedule an auto-quit timer for test runs.

    If the user interacts with the UI (keyboard/mouse), cancel the timer to
    avoid surprising exits during manual use.
    """
    # Priority: explicit CLI flag. Only honour env var in CI/pytest contexts
    env_ms = None
    if cli_ms is None and (os.getenv("PYTEST_CURRENT_TEST") or os.getenv("CI")):
        env_ms = os.getenv("SJN_AUTO_QUIT_MS")
    try:
        env_val = int(env_ms) if env_ms is not None else None
    except ValueError:
        env_val = None
    delay = cli_ms if cli_ms is not None else env_val
    if not delay or delay <= 0:
        return
    try:
        after_id = root.after(delay, lambda: root.quit())
        # Cancel on first user interaction
        def _cancel(_e=None):
            try:
                root.after_cancel(after_id)
            except Exception:
                pass
            try:
                root.unbind_all('<Any-KeyPress>')
                root.unbind_all('<Any-Button>')
                root.unbind_all('<Motion>')
            except Exception:
                pass
        root.bind_all('<Any-KeyPress>', _cancel, add=True)
        root.bind_all('<Any-Button>', _cancel, add=True)
        root.bind_all('<Motion>', _cancel, add=True)
    except Exception:
        pass


if __name__ == "__main__":
    args = _parse_args()
    if args.version:
        print(app_display_title())
        raise SystemExit(0)
    # Optional factory reset triggers (CLI or env var)
    try:
        env_reset = os.environ.get("SJN_FACTORY_RESET", "").strip().lower() in {"1", "true", "yes", "on"}
    except Exception:
        env_reset = False
    do_reset = bool(getattr(args, "factory_reset", False) or env_reset)
    if do_reset:
        try:
            perform_factory_reset(verbose=True)
        except Exception:
            pass
    # Monkey-patch tk.Tk to inject auto-quit scheduling after window creation
    _orig_tk = tk.Tk

    def _tk_factory(*a, **kw):
        r = _orig_tk(*a, **kw)
        _maybe_auto_quit(r, args.auto_quit_ms)
        return r

    tk.Tk = _tk_factory  # type: ignore[assignment]
    try:
        # Import the app entrypoint after monkey-patching Tk so any Tk() created
        # during module import will go through our factory (ensures auto-quit works).
        from sofa_jobs_navigator.app import run as app_run  # type: ignore
        app_run()
    finally:
        tk.Tk = _orig_tk  # restore
