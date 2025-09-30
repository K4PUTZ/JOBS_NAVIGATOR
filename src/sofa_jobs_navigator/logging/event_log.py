"""Structured event logger with verbose flag support."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from platformdirs import user_log_path
try:
    # Mirror errors to the plain console log for visibility
    from .console_file import CONSOLE_FILE_LOGGER
except Exception:  # pragma: no cover - optional import safeguard
    CONSOLE_FILE_LOGGER = None  # type: ignore

from ..config.flags import FlagSet, FLAGS

LOG_APP_NAME = "sofa_jobs_navigator"
LOG_FILE_NAME = "events.log"


class EventLogger:
    """Light-weight structured logger wrapped around ``logging``."""

    def __init__(self, *, flags: FlagSet = FLAGS, log_dir: Path | None = None) -> None:
        self._flags = flags
        self._log_dir = log_dir or user_log_path(LOG_APP_NAME)
        self._log_path = Path(self._log_dir) / LOG_FILE_NAME
        self._logger = logging.getLogger("sofa_jobs_event")
        self._configure()

    # =================== PUBLIC API ===================
    def info(self, message: str, **extra) -> None:
        self._logger.info(message, extra={"extra_data": extra})

    def warn(self, message: str, **extra) -> None:
        self._logger.warning(message, extra={"extra_data": extra})

    def error(self, message: str, **extra) -> None:
        self._logger.error(message, extra={"extra_data": extra})
        # Also mirror to console log for quick visibility
        try:
            if CONSOLE_FILE_LOGGER is not None:
                # Include minimal extra info inline if present
                if extra:
                    flat = ", ".join(f"{k}={v}" for k, v in extra.items())
                    CONSOLE_FILE_LOGGER.log_error(f"{message} ({flat})")
                else:
                    CONSOLE_FILE_LOGGER.log_error(message)
        except Exception:
            # Never let logging cause crashes
            pass

    def debug(self, message: str, **extra) -> None:
        if not self._flags.verbose_logging:
            return
        self._logger.debug(message, extra={"extra_data": extra})

    # =================== INTERNALS ===================
    def _configure(self) -> None:
        self._log_dir.mkdir(parents=True, exist_ok=True)
        for handler in list(self._logger.handlers):
            self._logger.removeHandler(handler)
        handler = RotatingFileHandler(self._log_path, maxBytes=512_000, backupCount=3)
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s %(extra_data)s')
        handler.setFormatter(formatter)
        self._logger.addHandler(handler)
        self._logger.setLevel(logging.DEBUG if self._flags.verbose_logging else logging.INFO)


LOGGER = EventLogger()

# =================== END EVENT LOGGER ===================
