"""Centralized app identity and version.

Update `VERSION` here to propagate across the UI.
"""

from __future__ import annotations

# Base app name (without registered sign, suitable for window titles)
APP_NAME: str = "Sofa Jobs Navigator"

# Branded app name (with registered sign for in-app branding labels)
APP_NAME_BRANDED: str = "Sofa Jobs Navigator\N{REGISTERED SIGN}"

# Human-visible version tag
VERSION: str = "beta 1.08"


def app_display_title() -> str:
    """Title string for window titles (no registered mark)."""
    return f"{APP_NAME} {VERSION}"


def app_display_brand() -> str:
    """Branded string for in-app labels (includes registered mark)."""
    return f"{APP_NAME_BRANDED} {VERSION}"
