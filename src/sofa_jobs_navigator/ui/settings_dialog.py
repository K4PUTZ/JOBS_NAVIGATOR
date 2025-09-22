"""Settings dialog implementation."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
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
        frame.columnconfigure(0, weight=1)
        # Header area (packed left) to avoid grid for top elements
        header = ttk.Frame(frame)
        header.grid(row=0, column=0, columnspan=3, sticky='w')

        # Working folder row
        wf_row = ttk.Frame(header)
        wf_row.pack(anchor='w')
        ttk.Label(wf_row, text='Working folder:').pack(side='left')
        self.working_var = tk.StringVar(value=self._settings.working_folder or '')
        self._working_entry = ttk.Entry(wf_row, textvariable=self.working_var, width=40, state='readonly', justify='left')
        self._working_entry.pack(side='left', padx=(6, 6))
        ttk.Button(wf_row, text='Browse…', command=self._pick_working_folder).pack(side='left')

        # Account row
        acct_row = ttk.Frame(header)
        acct_row.pack(anchor='w', pady=(6, 4))
        ttk.Label(acct_row, textvariable=self._account_var).pack(side='left')
        auth_btns = ttk.Frame(acct_row)
        auth_btns.pack(side='left', padx=(12, 0))
        ttk.Button(auth_btns, text='Connect / Refresh', command=self._on_auth_connect).pack(side='left', padx=(0, 6))
        ttk.Button(auth_btns, text='Clear Tokens', command=self._on_auth_clear).pack(side='left', padx=(0, 6))

        # Preferences row: Sounds on/off and Connect on Startup
        prefs_row = ttk.Frame(header)
        prefs_row.pack(anchor='w', pady=(2, 6))
        # Sounds toggle
        ttk.Label(prefs_row, text='Sounds:').pack(side='left')
        self._sounds_var = tk.BooleanVar(value=bool(self._settings.sounds_enabled))
        ttk.Checkbutton(prefs_row, variable=self._sounds_var, text='On').pack(side='left', padx=(6, 12))
        # Connect on startup toggle
        ttk.Label(prefs_row, text='Connect on Startup:').pack(side='left')
        self._connect_start_var = tk.BooleanVar(value=bool(getattr(self._settings, 'connect_on_startup', True)))
        ttk.Checkbutton(prefs_row, variable=self._connect_start_var, text='On').pack(side='left', padx=(6, 0))

        # Tip + reset help row
        tip_row = ttk.Frame(header)
        tip_row.pack(anchor='w', pady=(4, 0))
        ttk.Label(tip_row, text='Tip: You can reset in-product help messages here.', foreground='#6c757d').pack(side='left')
        ttk.Button(tip_row, text='Reset Welcome Screen', command=self._reset_welcome).pack(side='left', padx=(12, 0))
        # Backing var for show_help_on_startup (also saved on Save)
        self._show_help_var = tk.BooleanVar(value=bool(getattr(self._settings, 'show_help_on_startup', True)))

        # Separator before favorites
        ttk.Separator(frame, orient='horizontal').grid(row=1, column=0, columnspan=3, sticky='ew', pady=(8, 6))

        ttk.Label(frame, text='Favorites:').grid(row=2, column=0, sticky='w', pady=(0, 6))

        # Favorites table
        fav_frame = ttk.Frame(frame)
        fav_frame.grid(row=3, column=0, columnspan=3, sticky='ew')
        # Columns: [#] [SKU/] [Relative Path] [Button Label]
        fav_frame.columnconfigure(0, weight=0)
        fav_frame.columnconfigure(1, weight=0)
        fav_frame.columnconfigure(2, weight=1)
        fav_frame.columnconfigure(3, weight=1)

        # Header row
        ttk.Label(fav_frame, text='Relative Path:').grid(row=0, column=2, sticky='w', padx=(4, 4), pady=(0, 2))
        ttk.Label(fav_frame, text='Button Label:').grid(row=0, column=3, sticky='w', padx=(4, 0), pady=(0, 2))

        for idx, fav in enumerate(self._settings.favorites, start=1):
            r = idx  # data rows start at 1
            ttk.Label(fav_frame, text=f'{idx}.').grid(row=r, column=0, sticky='e', padx=(0, 4), pady=2)
            ttk.Label(fav_frame, text='SKU/').grid(row=r, column=1, sticky='e', padx=(0, 4), pady=2)
            path_var = tk.StringVar(value=fav.path)
            label_var = tk.StringVar(value=fav.label)
            ttk.Entry(fav_frame, textvariable=path_var, width=32).grid(row=r, column=2, sticky='ew', padx=(4, 4), pady=2)
            ttk.Entry(fav_frame, textvariable=label_var, width=24).grid(row=r, column=3, sticky='ew', padx=(4, 0), pady=2)
            # Keep storage order (label, path) to satisfy save handler
            self._favorite_vars.append((label_var, path_var))

        btns = ttk.Frame(frame)
        btns.grid(row=4, column=0, columnspan=3, pady=(12, 0))
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
        favorites: list[Favorite] = []
        # Validate favorites before saving
        for idx, (label_var, path_var) in enumerate(self._favorite_vars, start=1):
            label = (label_var.get() or '').strip()
            path = (path_var.get() or '').strip()
            # Path but no label: block save and ask user to provide a name
            if path and not label:
                messagebox.showerror(
                    title='Favorite needs a name',
                    message=(
                        f'Favorite {idx} has a path configured but no name.\n'
                        'Please enter a label for this shortcut.'
                    ),
                    parent=self,
                )
                return
            # Label but no path: confirm it will open the SKU root
            if label and not path:
                proceed = messagebox.askyesno(
                    title='No path set for favorite',
                    message=(
                        f'Favorite {idx} has a label but no path.\n'
                        'This shortcut will open the SKU root. Do you want to continue?'
                    ),
                    parent=self,
                )
                if not proceed:
                    return
            favorites.append(Favorite(label=label, path=path))
        updated = Settings(
            favorites=favorites,
            working_folder=self.working_var.get() or None,
            save_recent_skus=self._settings.save_recent_skus,
            sounds_enabled=bool(self._sounds_var.get()) if hasattr(self, '_sounds_var') else self._settings.sounds_enabled,
            connect_on_startup=bool(self._connect_start_var.get()) if hasattr(self, '_connect_start_var') else getattr(self._settings, 'connect_on_startup', True),
            recent_skus=self._settings.recent_skus,
            show_help_on_startup=bool(self._show_help_var.get()) if hasattr(self, '_show_help_var') else getattr(self._settings, 'show_help_on_startup', True),
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

    def _reset_welcome(self) -> None:
        try:
            self._show_help_var.set(True)
            messagebox.showinfo(title='Welcome Screen', message='Welcome screen will show on next start.', parent=self)
        except Exception:
            pass


# =================== END SETTINGS DIALOG ===================
