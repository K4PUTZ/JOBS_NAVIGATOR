"""Icon helpers for Sofa Jobs Navigator.

Adapted from DRIVE_OPERATOR.utils.set_app_icon to locate and apply window icons
from available PNG/ICO resources in this workspace.
"""

from __future__ import annotations

import os
import sys
import platform
import tkinter as tk

try:
    # Optional: if Pillow is available we can convert/shape icons for macOS
    from PIL import Image, ImageTk, ImageDraw  # type: ignore
except Exception:  # Pillow is optional
    Image = None  # type: ignore
    ImageTk = None  # type: ignore


def resource_path(relative_path: str) -> str:
    """Get absolute path to resource, works for dev and for PyInstaller."""
    base_path = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base_path, relative_path)


def set_app_icon(window: tk.Misc) -> None:
    """Set the application icon where possible.

    Behavior:
    - Windows: prefer `.ico` via `iconbitmap` (taskbar + window). If `.png` exists, also set via `iconphoto`.
    - macOS/Linux: prefer `.png` via `iconphoto`. If only `.ico` is available and Pillow is installed,
      convert in-memory to a PhotoImage and apply via `iconphoto`.
    Searches for common icon file names in both this project and DRIVE_OPERATOR.
    """

    icon_candidates = [
        # Prefer PNGs
        "sofa_icon.png",
        os.path.join("JOBS NAVIGATOR", "sofa_icon.png"),
        os.path.join("JOBS_NAVIGATOR", "sofa_icon.png"),
        os.path.join("DRIVE_OPERATOR", "sofa_icon.png"),
        # Fallback smaller PNG if the main one is missing
        "sofa_icon_128.png",
        os.path.join("JOBS NAVIGATOR", "sofa_icon_128.png"),
        os.path.join("JOBS_NAVIGATOR", "sofa_icon_128.png"),
        os.path.join("DRIVE_OPERATOR", "sofa_icon_128.png"),
        # ICO fallbacks (mostly for Windows)
        "sofa_icon.ico",
        os.path.join("JOBS NAVIGATOR", "sofa_icon.ico"),
        os.path.join("JOBS_NAVIGATOR", "sofa_icon.ico"),
        os.path.join("DRIVE_OPERATOR", "sofa_icon.ico"),
        os.path.join("NAVIGATOR", "sofa_icon.ico"),
    ]

    ico_path = None
    png_path = None
    for cand in icon_candidates:
        p = resource_path(cand)
        if os.path.exists(p):
            if p.lower().endswith(".png") and png_path is None:
                png_path = p
            if p.lower().endswith(".ico") and ico_path is None:
                ico_path = p
    system = platform.system()

    # Try best option per platform
    try:
        if system == "Windows":
            # Use the .ico for proper taskbar icon if available
            if ico_path:
                try:
                    # Only Tk supports iconbitmap; for Toplevel use iconphoto
                    if hasattr(window, "iconbitmap"):
                        window.iconbitmap(ico_path)  # type: ignore[call-arg]
                except Exception:
                    pass
            # If a PNG is available, also set iconphoto for Tk widgets
            if png_path:
                try:
                    img = tk.PhotoImage(file=png_path)
                    if hasattr(window, "iconphoto"):
                        window.iconphoto(True, img)  # type: ignore[misc]
                        setattr(window, "_iconphoto_ref", img)
                except Exception:
                    pass
        else:
            # Non-Windows (macOS/Linux): prefer PNG via iconphoto
            if png_path:
                # On macOS, shrink content and round corners to match system look
                if system == "Darwin" and Image is not None and ImageTk is not None:
                    try:
                        pil = Image.open(png_path).convert("RGBA")
                        size = max(pil.width, pil.height)
                        canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
                        inset = int(size * 0.08)
                        target = size - inset * 2
                        pil_resized = pil.resize((target, target), Image.LANCZOS)
                        radius = int(size * 0.18)
                        mask = Image.new("L", (target, target), 0)
                        drw = ImageDraw.Draw(mask)
                        drw.rounded_rectangle((0, 0, target, target), radius=radius, fill=255)
                        canvas.paste(pil_resized, (inset, inset), mask)
                        bio_img = ImageTk.PhotoImage(canvas)
                        if hasattr(window, "iconphoto"):
                            window.iconphoto(True, bio_img)  # type: ignore[misc]
                            setattr(window, "_iconphoto_ref", bio_img)
                            return
                    except Exception:
                        pass
                # Generic PNG path
                try:
                    img = tk.PhotoImage(file=png_path)
                    if hasattr(window, "iconphoto"):
                        window.iconphoto(True, img)  # type: ignore[misc]
                        setattr(window, "_iconphoto_ref", img)
                        return
                except Exception:
                    pass
            # If only ICO exists and Pillow is available, convert in-memory
            if ico_path and Image is not None and ImageTk is not None:
                try:
                    im = Image.open(ico_path)
                    photo = ImageTk.PhotoImage(im)
                    if hasattr(window, "iconphoto"):
                        window.iconphoto(True, photo)  # type: ignore[misc]
                        setattr(window, "_iconphoto_ref", photo)
                except Exception:
                    pass
    except Exception:
        # Never crash the app due to icon issues
        pass
