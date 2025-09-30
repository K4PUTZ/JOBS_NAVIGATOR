"""Simple console log writer stored at project root."""

from __future__ import annotations

import datetime as _dt
import os
import subprocess
import sys
from pathlib import Path
from platformdirs import user_log_path
from typing import Optional


_PROJECT_ROOT = Path(__file__).resolve().parents[3]
# Default to user log directory to avoid permissions issues on installed packages
_DEFAULT_LOG_DIR = user_log_path("sofa_jobs_navigator")
_DEFAULT_LOG_PATH = _DEFAULT_LOG_DIR / "console_log.txt"
# Backwards-compatibility: if a legacy project-root log exists, keep writing there
_LEGACY_LOG_PATH = _PROJECT_ROOT / "console_log.txt"


class ConsoleFileLogger:
    """Append console events to a plain-text log at the project root."""

    def __init__(self, path: Path | None = None) -> None:
        if path is not None:
            self._path = path
        else:
            # Prefer legacy location only if it already exists; otherwise use user log dir
            self._path = _LEGACY_LOG_PATH if _LEGACY_LOG_PATH.exists() else _DEFAULT_LOG_PATH
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._last_logged_date: Optional[_dt.date] = None
        # Track last account logged for the current date to avoid duplicates
        self._last_account_for_date: Optional[str] = None
        self._initialise_last_logged_date()

    @property
    def path(self) -> Path:
        return self._path

    # ------------------ Public logging API ------------------
    def log_sku(self, sku: str) -> None:
        if not sku:
            return
        self._write_entry("SKU", f"Detected SKU: {sku}")

    def log_error(self, message: str) -> None:
        if not message:
            return
        self._write_entry("ERROR", message)

    def log_info(self, message: str) -> None:
        if not message:
            return
        self._write_entry("INFO", message)

    def log_account(self, account: str | None, *, session: int | None = None) -> None:
        """Log the authenticated account once per day unless a new account appears.

        - Skips logging when ``account`` is empty/None (avoids noise on sign-out).
        - Includes ``session`` number tag when provided.
        """
        if not account:
            return
        label = str(account)
        today = _dt.date.today()
        # If same day and same account already logged, skip
        if self._last_logged_date == today and self._last_account_for_date == label:
            return
        msg = f"Authenticated account: {label}"
        if session is not None:
            msg += f" (session {session})"
        self._write_entry("ACCOUNT", msg)
        self._last_logged_date = today
        self._last_account_for_date = label

    # ------------------ Internal helpers ------------------
    def _write_entry(self, category: str, message: str) -> None:
        now = _dt.datetime.now()
        self._ensure_day_separator(now.date())
        line = f"[{now.strftime('%H:%M:%S')}] [{category}] {message}\n"
        with self._path.open("a", encoding="utf-8") as fh:
            fh.write(line)

    def _ensure_day_separator(self, current_date: _dt.date) -> None:
        if self._last_logged_date == current_date:
            return
        separator = f"======== {current_date.isoformat()} - {current_date.strftime('%A')} ========\n"
        with self._path.open("a", encoding="utf-8") as fh:
            fh.write("\n" if self._path.exists() and self._path.stat().st_size else "")
            fh.write(separator)
        self._last_logged_date = current_date

    def _initialise_last_logged_date(self) -> None:
        if not self._path.exists():
            return
        try:
            current_section_date: Optional[_dt.date] = None
            with self._path.open("r", encoding="utf-8") as fh:
                for raw in fh:
                    line = raw.strip()
                    # Day separator
                    if line.startswith("========") and line.endswith("========"):
                        middle = line.strip("=").strip()
                        date_part = middle.split(" - ")[0].strip()
                        try:
                            current_section_date = _dt.date.fromisoformat(date_part)
                            self._last_logged_date = current_section_date
                            # Reset last account for new date section; will set when we see ACCOUNT entry
                            self._last_account_for_date = None
                        except ValueError:
                            continue
                        continue
                    # Detect ACCOUNT lines within the current section
                    if current_section_date is not None and "[ACCOUNT]" in line:
                        # Example line: [12:34:56] [ACCOUNT] Authenticated account: user@example.com (session 5)
                        try:
                            after_tag = line.split("[ACCOUNT]", 1)[1].strip()
                            if after_tag.lower().startswith("authenticated account:"):
                                content = after_tag.split(":", 1)[1].strip()
                                # Extract the account before optional session suffix
                                acct = content.split(" (session", 1)[0].strip()
                                self._last_account_for_date = acct or None
                        except Exception:
                            pass
        except Exception:
            # If anything goes wrong just reset so the next write adds a fresh separator
            self._last_logged_date = None
            self._last_account_for_date = None


def open_console_log_file(path: Path | None = None) -> None:
    """Open the console log in the system's default text editor."""

    target = path or CONSOLE_FILE_LOGGER.path
    try:
        target.touch(exist_ok=True)
    except Exception:
        # Best effort: if touch fails there's nothing else we can do
        return

    if sys.platform == "darwin":
        subprocess.run(["open", str(target)], check=False)
    elif os.name == "nt":  # Windows
        os.startfile(str(target))  # type: ignore[attr-defined]
    else:
        subprocess.run(["xdg-open", str(target)], check=False)


CONSOLE_FILE_LOGGER = ConsoleFileLogger()

"""Shared logger instance for modules to import."""
