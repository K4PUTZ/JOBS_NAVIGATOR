"""Settings dialog implementation."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, filedialog
from typing import Callable
import os

from ..config.settings import Favorite, Settings

# =================== SETTINGS DIALOG ===================
# Provides a modal window for editing favorites and toggles.
# --------------------------------------------------------


class SettingsDialog(tk.Toplevel):
    def __init__(
        self,
        master: tk.Misc,
        *,
        settings: Settings,
        on_save: Callable[[Settings], None],
        on_auth_connect: Callable[[], None],
        on_auth_clear: Callable[[], None],
        current_account: str | None = None,
    ) -> None:
        super().__init__(master)
        self.title('Settings')
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()
        self._settings = settings
        self._on_save = on_save
        self._on_auth_connect = on_auth_connect
        self._on_auth_clear = on_auth_clear
        self._current_account = current_account
        self._favorite_vars: list[tuple[tk.StringVar, tk.StringVar]] = []
        self._account_var = tk.StringVar(value=self._format_account(self._current_account))
        self._build_ui()
        self._center_on_screen()

    def _build_ui(self) -> None:
        frame = ttk.Frame(self, padding=12)
        frame.pack(fill='both', expand=True)
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text='Working folder:').grid(row=0, column=0, sticky='w')
        self.working_var = tk.StringVar(value=self._settings.working_folder or '')
        # Read-only display of current folder + Browse button
        self._working_entry = ttk.Entry(frame, textvariable=self.working_var, width=40, state='readonly')
        self._working_entry.grid(row=0, column=1, sticky='ew')
        ttk.Button(frame, text='Browse…', command=self._pick_working_folder).grid(row=0, column=2, padx=(6, 0))

        ttk.Label(frame, textvariable=self._account_var).grid(row=1, column=0, sticky='w', pady=(6, 4))
        auth_btns = ttk.Frame(frame)
        auth_btns.grid(row=1, column=1, sticky='e', pady=(6, 4))
        ttk.Button(auth_btns, text='Connect / Refresh', command=self._on_auth_connect).pack(side='left', padx=(0, 6))
        ttk.Button(auth_btns, text='Clear Tokens', command=self._on_auth_clear).pack(side='left', padx=(0, 6))

        ttk.Label(frame, text='Favorites').grid(row=2, column=0, sticky='w', pady=(12, 4))
        fav_frame = ttk.Frame(frame)
        fav_frame.grid(row=3, column=0, columnspan=2)
        for idx, fav in enumerate(self._settings.favorites, start=1):
            row = ttk.Frame(fav_frame)
            row.pack(fill='x', pady=2)
            ttk.Label(row, text=f'{idx}.').pack(side='left')
            label_var = tk.StringVar(value=fav.label)
            path_var = tk.StringVar(value=fav.path)
            ttk.Entry(row, textvariable=label_var, width=20).pack(side='left', padx=(4, 4))
            ttk.Entry(row, textvariable=path_var, width=30).pack(side='left', padx=(4, 4))
            self._favorite_vars.append((label_var, path_var))

        btns = ttk.Frame(frame)
        btns.grid(row=4, column=0, columnspan=2, pady=(12, 0))
        ttk.Button(btns, text='Save', command=self._on_press_save).pack(side='right')
        ttk.Button(btns, text='Cancel', command=self.destroy).pack(side='right', padx=(0, 6))

    def _pick_working_folder(self) -> None:
        current = self.working_var.get() or os.path.expanduser('~')
        try:
            chosen = filedialog.askdirectory(parent=self, initialdir=current, title='Select working folder', mustexist=True)
        except TypeError:
            # Some Tk versions may not support mustexist; fall back gracefully
            chosen = filedialog.askdirectory(parent=self, initialdir=current, title='Select working folder')
        if chosen:
            # Update the read-only entry by temporarily enabling it
            self._working_entry.configure(state='normal')
            self.working_var.set(chosen)
            self._working_entry.configure(state='readonly')

    def _on_press_save(self) -> None:
        favorites = []
        for label_var, path_var in self._favorite_vars:
            favorites.append(Favorite(label=label_var.get(), path=path_var.get()))
        updated = Settings(
            favorites=favorites,
            working_folder=self.working_var.get() or None,
            save_recent_skus=self._settings.save_recent_skus,
            sounds_enabled=self._settings.sounds_enabled,
            recent_skus=self._settings.recent_skus,
        )
        self._on_save(updated)
        self.destroy()

    def _format_account(self, account: str | None) -> str:
        return f'Account: {account or "(unauthenticated)"}'

    def set_account(self, account: str | None) -> None:
        """Update the account label live (called after successful connect/clear)."""
        try:
            self._current_account = account
            self._account_var.set(self._format_account(account))
        except Exception:
            pass

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


# =================== END SETTINGS DIALOG ===================
