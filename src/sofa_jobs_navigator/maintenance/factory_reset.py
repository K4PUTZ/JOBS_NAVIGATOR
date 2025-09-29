"""Factory reset utilities for Sofa Jobs Navigator.

Removes user settings, tokens, and logs so the app starts fresh and
shows the Welcome window on next launch.
"""

from __future__ import annotations

from pathlib import Path
import os
import shutil
import sys
from platformdirs import user_config_path, user_log_path

CONFIG_APP_NAME = "sofa_jobs_navigator"


def _safe_remove(path: Path) -> None:
    try:
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
        elif path.exists():
            path.unlink(missing_ok=True)
    except Exception:
        pass


def perform_factory_reset(*, verbose: bool = False) -> None:
    """Delete config, tokens, recents and logs.

    Keeps credentials.json (OAuth client) in place if present.
    """

    cfg_dir = user_config_path(CONFIG_APP_NAME)
    log_dir = user_log_path(CONFIG_APP_NAME)

    # Remove preference files (but not credentials.json)
    for name in ("config.json", "token.json", "account.json"):
        _safe_remove(Path(cfg_dir) / name)

    # Clear logs directory completely (console + events)
    _safe_remove(Path(log_dir))

    # Best-effort: clear legacy console_log.txt if it exists nearby
    try:
        # 1) Next to executable (PyInstaller onedir)
        exe_dir = Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
        _safe_remove(exe_dir / "console_log.txt")
    except Exception:
        pass

    # Ensure dirs exist again (empty) so app can write immediately
    try:
        Path(cfg_dir).mkdir(parents=True, exist_ok=True)
        Path(log_dir).mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

    if verbose:
        print("[Factory Reset] Cleared config (except credentials.json) and logs.")


# =================== END FACTORY RESET ===================

