"""Shortcut picker dialog."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable, Iterable

from ..config.settings import Favorite

# =================== SHORTCUT PICKER ===================
# Displays a list of favorites and allows selection via button or numeric key.
# -------------------------------------------------------


class ShortcutPicker(tk.Toplevel):
    def __init__(
        self,
        master: tk.Misc,
        *,
        favorites: Iterable[Favorite],
        on_pick: Callable[[Favorite], None],
    ) -> None:
        super().__init__(master)
        self.title('Choose Shortcut')
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()
        self._on_pick = on_pick
        self._favorites = list(favorites)
        self._build_ui()
        self._center_on_screen()

    def _build_ui(self) -> None:
        frame = ttk.Frame(self, padding=12)
        frame.pack(fill='both', expand=True)
        for idx, fav in enumerate(self._favorites, start=1):
            label = fav.label or f'Favorite {idx}'
            btn = ttk.Button(frame, text=f'({idx}) - {label}', command=lambda f=fav: self._choose(f))
            btn.pack(fill='x', pady=2)
            self.bind(str(idx), lambda event, f=fav: self._choose(f))
        ttk.Button(frame, text='Cancel', command=self.destroy).pack(fill='x', pady=(8, 0))

    def _choose(self, favorite: Favorite) -> None:
        self._on_pick(favorite)
        self.destroy()

    def _center_on_screen(self) -> None:
        try:
            self.update_idletasks()
            w = self.winfo_width() or self.winfo_reqwidth()
            h = self.winfo_height() or self.winfo_reqheight()
            sw = self.winfo_screenwidth()
            sh = self.winfo_screenheight()
            x = max((sw // 2) - (w // 2), 0)
            y = max((sh // 2) - (h // 2), 0)
            self.geometry(f"{w}x{h}+{x}+{y}")
        except Exception:
            pass


# =================== END SHORTCUT PICKER ===================
