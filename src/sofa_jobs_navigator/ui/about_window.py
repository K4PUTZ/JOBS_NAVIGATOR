"""About window for Sofa Jobs Navigator."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from . import about_window as _self_module  # avoid relative confusion for mypy
from ..utils.app_icons import set_app_icon


class AboutWindow(tk.Toplevel):
    """Small About dialog reproducing the logo and showing credits text."""

    def __init__(self, master: tk.Misc | None = None) -> None:
        super().__init__(master)
        self.title('About — Sofa Jobs Navigator')
        self.resizable(False, False)
        self.configure(padx=12, pady=12)
        try:
            self.transient(master)
        except Exception:
            pass
        # Build UI
        self._build_ui()
        # Set window icon
        try:
            set_app_icon(self)
        except Exception:
            pass
        # Center relative to parent if possible
        try:
            self.update_idletasks()
            if master is not None:
                mx = master.winfo_rootx()
                my = master.winfo_rooty()
                mw = master.winfo_width()
                mh = master.winfo_height()
                w = 400  # fixed width per request
                h = self.winfo_height()
                x = mx + (mw - w) // 2
                y = my + (mh - h) // 2
                self.geometry(f"{w}x{h}+{max(0, x)}+{max(0, y)}")
        except Exception:
            pass

    def _build_ui(self) -> None:
        # Top branding: replicate main logo (touching squares) and program name below
        brand = ttk.Frame(self)
        brand.pack(fill='x', anchor='w')

        row0 = ttk.Frame(brand)
        row0.pack(side='top', anchor='w', padx=(5, 0))  # 5px left padding to match main window
        colors = ['#ffd400', '#00e5ff', '#39ff14', '#ff00ff', '#ff3b30', '#007aff']
        for c in colors:
            sq = tk.Frame(row0, width=12, height=12, background=c, highlightthickness=0, bd=0)
            sq.pack(side='left', padx=0)

        # Two spacer lines between squares and program name (mirror main window)
        ttk.Frame(brand, height=4).pack(side='top', anchor='w')
        ttk.Frame(brand, height=4).pack(side='top', anchor='w')
        ttk.Label(brand, text='Sofa Jobs Navigator® 1.0').pack(side='top', anchor='w', padx=(5, 0))

        # Requested spacing: 5 empty lines below
        for _ in range(5):
            ttk.Frame(self, height=8).pack(fill='x')

        # Credits text
        credits = (
            "Mateus O. S. Ribeiro\n"
            "emaildomat@gmail.com\n"
            "GPT-5 Agent generated\n"
            "September 2025\n"
            "Sofa Digital\n"
            "All Rights Reserved"
        )
        lbl = ttk.Label(self, text=credits, justify='left')
        lbl.pack(anchor='w', padx=(5, 0))

        # Close button at bottom-right
        btn_row = ttk.Frame(self)
        btn_row.pack(fill='x', pady=(12, 0))
        ttk.Frame(btn_row).pack(side='left', expand=True)
        close_btn = ttk.Button(btn_row, text='Close', command=self.destroy)
        close_btn.pack(side='right')
