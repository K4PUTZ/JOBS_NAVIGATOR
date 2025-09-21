"""Centralized runtime flags for Sofa Jobs Navigator.

Use these toggles to control diagnostics, offline modes, and testing hooks.
Consumers should import from here rather than hard-coding their own environment reads.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

# =================== FLAG DEFINITIONS ===================
# Each flag pulls from an environment variable first, then falls back to a default.
# Update the defaults conservatively so production builds stay quiet by default.
# --------------------------------------------------------

@dataclass(frozen=True)
class FlagSet:
    """Structured view of all debug/test flags."""

    verbose_logging: bool
    offline_mode: bool
    config_dry_run: bool
    ui_debug: bool
    mute_sounds: bool
    mock_clipboard: str | None
    test_hotkey: str | None


def _env_bool(name: str, default: bool = False) -> bool:
    """Parse an environment variable into a boolean."""

    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_str(name: str) -> str | None:
    """Return the raw string value or ``None`` when unset/empty."""

    raw = os.environ.get(name)
    if raw is None:
        return None
    raw = raw.strip()
    return raw or None


# --------------- FLAG MATERIALIZATION ---------------
# Update this function if new flags are introduced. Downstream code should
# always call ``load_flags()`` at start-up and pass the dataclass around.
# ----------------------------------------------------

def load_flags() -> FlagSet:
    """Load all runtime flags from the environment."""

    return FlagSet(
        verbose_logging=_env_bool("SJN_VERBOSE", False),
        offline_mode=_env_bool("SJN_OFFLINE", False),
        config_dry_run=_env_bool("SJN_CONFIG_DRY_RUN", False),
        ui_debug=_env_bool("SJN_UI_DEBUG", False),
        mute_sounds=_env_bool("SJN_MUTE_SOUNDS", False),
        mock_clipboard=_env_str("SJN_MOCK_CLIPBOARD"),
        test_hotkey=_env_str("SJN_TEST_HOTKEY"),
    )


FLAGS = load_flags()


# =================== END FLAG DEFINITIONS ===================
# Import ``FLAGS`` for a ready-to-use singleton, or re-run ``load_flags``
# after mutating the environment during tests.
# ============================================================
