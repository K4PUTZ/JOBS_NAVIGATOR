"""Settings dialog implementation."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from typing import Callable
from pathlib import Path
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
        self._center_on_parent_or_screen()

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
        # Clear working folder button
        ttk.Button(wf_row, text='Clear', command=self._clear_working_folder).pack(side='left', padx=(6, 0))

        # Account row
        acct_row = ttk.Frame(header)
        acct_row.pack(anchor='w', pady=(6, 4))
        ttk.Label(acct_row, textvariable=self._account_var).pack(side='left')
        auth_btns = ttk.Frame(acct_row)
        auth_btns.pack(side='left', padx=(12, 0))
        ttk.Button(auth_btns, text='Connect / Refresh', command=self._on_auth_connect).pack(side='left', padx=(0, 6))
        ttk.Button(auth_btns, text='Clear Tokens', command=self._on_auth_clear).pack(side='left', padx=(0, 6))

        # Preferences: each control on its own line, with inverted label/checkbox style
        # 1) Sounds On
        sounds_row = ttk.Frame(header)
        sounds_row.pack(anchor='w', pady=(2, 2))
        self._sounds_var = tk.BooleanVar(value=bool(self._settings.sounds_enabled))
        _cb_sounds = ttk.Checkbutton(sounds_row, variable=self._sounds_var)
        _cb_sounds.pack(side='left', padx=(0, 6))
        ttk.Label(sounds_row, text='Sounds On.').pack(side='left')
        # 1.5) Show Welcome Window on Startup
        welcome_row = ttk.Frame(header)
        welcome_row.pack(anchor='w', pady=(2, 2))
        self._show_welcome_var = tk.BooleanVar(value=bool(getattr(self._settings, 'show_help_on_startup', True)))
        _cb_welcome = ttk.Checkbutton(welcome_row, variable=self._show_welcome_var)
        _cb_welcome.pack(side='left', padx=(0, 6))
        ttk.Label(welcome_row, text='Show Welcome Window on Startup.').pack(side='left')
        # 2) Connect on Startup (one line down)
        conn_row = ttk.Frame(header)
        conn_row.pack(anchor='w', pady=(2, 2))
        self._connect_start_var = tk.BooleanVar(value=bool(getattr(self._settings, 'connect_on_startup', False)))
        _cb_connect = ttk.Checkbutton(conn_row, variable=self._connect_start_var)
        _cb_connect.pack(side='left', padx=(0, 6))
        ttk.Label(conn_row, text='Connect on Startup.').pack(side='left')
        # 3) Prompt to connect on Startup when not connected
        prompt_row = ttk.Frame(header)
        prompt_row.pack(anchor='w', pady=(2, 2))
        self._prompt_connect_var = tk.BooleanVar(value=bool(getattr(self._settings, 'prompt_for_connect_on_startup', True)))
        _cb_prompt_connect = ttk.Checkbutton(prompt_row, variable=self._prompt_connect_var)
        _cb_prompt_connect.pack(side='left', padx=(0, 6))
        ttk.Label(prompt_row, text='Prompt to connect on Startup.').pack(side='left')
        # Disable prompt option when auto-connect is enabled
        def _sync_prompt_state(*_a):
            try:
                if bool(self._connect_start_var.get()):
                    _cb_prompt_connect.state(['disabled'])
                else:
                    _cb_prompt_connect.state(['!disabled'])
            except Exception:
                pass
        try:
            _sync_prompt_state()
            self._connect_start_var.trace_add('write', lambda *_: _sync_prompt_state())
        except Exception:
            pass
        # 4) Auto-search clipboard after connecting on startup
        auto_row = ttk.Frame(header)
        auto_row.pack(anchor='w', pady=(2, 2))
        self._auto_search_after_var = tk.BooleanVar(value=bool(getattr(self._settings, 'auto_search_clipboard_after_connect', False)))
        _cb_auto_search = ttk.Checkbutton(auto_row, variable=self._auto_search_after_var)
        _cb_auto_search.pack(side='left', padx=(0, 6))
        ttk.Label(auto_row, text='Auto-search clipboard after connect.').pack(side='left')
        # 5) Auto-load multi SKUs without prompt
        multi_row = ttk.Frame(header)
        multi_row.pack(anchor='w', pady=(2, 2))
        self._auto_load_multi_var = tk.BooleanVar(value=bool(getattr(self._settings, 'auto_load_multi_skus_without_prompt', False)))
        _cb_auto_load_multi = ttk.Checkbutton(multi_row, variable=self._auto_load_multi_var)
        _cb_auto_load_multi.pack(side='left', padx=(0, 6))
        ttk.Label(multi_row, text='Auto-load multiple SKUs (no prompt).').pack(side='left')
        # 6) Open root folder on SKU found (existing option)
        open_row = ttk.Frame(header)
        open_row.pack(anchor='w', pady=(2, 6))
        self._open_root_var = tk.BooleanVar(value=bool(getattr(self._settings, 'open_root_on_sku_found', False)))
        _cb_open_root = ttk.Checkbutton(open_row, variable=self._open_root_var)
        _cb_open_root.pack(side='left', padx=(0, 6))
        ttk.Label(open_row, text='Open root folder on SKU found.').pack(side='left')

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
        # Prepare a style that blends disabled entry background with dialog background (transparent-like)
        try:
            style = ttk.Style(self)
            bg = style.lookup('TFrame', 'background') or self.cget('bg') or '#f0f0f0'
            style.configure('Sofa.Disabled.TEntry', fieldbackground=bg, background=bg, foreground='#6c757d')
            style.map('Sofa.Disabled.TEntry', fieldbackground=[('disabled', bg)], foreground=[('disabled', '#6c757d')])
        except Exception:
            style = None  # type: ignore[assignment]

        # Header row
        ttk.Label(fav_frame, text='Relative Path:').grid(row=0, column=2, sticky='w', padx=(4, 4), pady=(0, 2))
        ttk.Label(fav_frame, text='Button Label:').grid(row=0, column=3, sticky='w', padx=(4, 0), pady=(0, 2))

        for idx, fav in enumerate(self._settings.favorites, start=1):
            r = idx  # data rows start at 1
            ttk.Label(fav_frame, text=f'(F{idx})').grid(row=r, column=0, sticky='e', padx=(0, 4), pady=2)
            ttk.Label(fav_frame, text='SKU/').grid(row=r, column=1, sticky='e', padx=(0, 4), pady=2)
            path_var = tk.StringVar(value=fav.path)
            label_var = tk.StringVar(value=fav.label)
            path_entry = ttk.Entry(fav_frame, textvariable=path_var, width=32)
            label_entry = ttk.Entry(fav_frame, textvariable=label_var, width=24)
            # F1 is fixed to ROOT: disable both fields for reference only
            if idx == 1:
                try:
                    # Show placeholder text in path, but save as root (empty) later
                    path_var.set('F1 always opens the root folder.')
                    # Disable and remove from focus traversal
                    path_entry.configure(state='disabled', takefocus=0)
                    label_entry.configure(state='disabled', takefocus=0)
                    # Apply transparent-like style if available
                    if style is not None:
                        path_entry.configure(style='Sofa.Disabled.TEntry')
                        label_entry.configure(style='Sofa.Disabled.TEntry')
                except Exception:
                    pass
            path_entry.grid(row=r, column=2, sticky='ew', padx=(4, 4), pady=2)
            label_entry.grid(row=r, column=3, sticky='ew', padx=(4, 0), pady=2)
            # Keep storage order (label, path) to satisfy save handler
            self._favorite_vars.append((label_var, path_var))

        # After the favorites section: two empty lines
        try:
            ttk.Frame(frame, height=8).grid(row=4, column=0, sticky='ew')
            ttk.Frame(frame, height=8).grid(row=5, column=0, sticky='ew')
        except Exception:
            pass
        # Warning text
        try:
            warn_text = 'Warning: ensure the path reflects the exact same pattern of the remote folders.'
            ttk.Label(frame, text=warn_text, justify='left').grid(row=6, column=0, sticky='w', pady=(0, 6))
        except Exception:
            pass
        # Two empty lines above the image (directly beneath the warning)
        try:
            ttk.Frame(frame, height=8).grid(row=7, column=0, sticky='ew')
            ttk.Frame(frame, height=8).grid(row=8, column=0, sticky='ew')
        except Exception:
            pass
        # Favorites.png image underneath (from help assets folder)
        self._fav_image_ref = None  # keep a reference alive
        try:
            base = Path(__file__).resolve().parent / 'assets' / 'help'
            img_path = base / 'Favorites.png'
            if img_path.exists():
                try:
                    from PIL import Image, ImageTk  # type: ignore
                    im = Image.open(str(img_path))
                    # Optionally, constrain a maximum width to fit dialog if needed
                    max_w = 560
                    if im.width > max_w:
                        ratio = max_w / float(im.width)
                        im = im.resize((int(im.width * ratio), int(im.height * ratio)), getattr(Image, 'LANCZOS', 1))
                    self._fav_image_ref = ImageTk.PhotoImage(im)
                except Exception:
                    try:
                        # Fallback to Tk PhotoImage for PNG
                        self._fav_image_ref = tk.PhotoImage(file=str(img_path))
                    except Exception:
                        self._fav_image_ref = None
                if self._fav_image_ref is not None:
                    # Center the image (omit sticky to center in cell)
                    tk.Label(frame, image=self._fav_image_ref, bd=0).grid(row=9, column=0, pady=(0, 6))
        except Exception:
            self._fav_image_ref = None

        # Buttons row (moved below the new content)
        btns = ttk.Frame(frame)
        btns.grid(row=10, column=0, columnspan=3, pady=(12, 0))
        # Save/Cancel on the right (update functionality not yet implemented)
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
            # F1 is permanently ROOT: force empty path and skip warnings
            if idx == 1:
                path = ''
                favorites.append(Favorite(label=label, path=path))
                continue
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
            connect_on_startup=bool(self._connect_start_var.get()) if hasattr(self, '_connect_start_var') else getattr(self._settings, 'connect_on_startup', False),
            prompt_for_connect_on_startup=bool(self._prompt_connect_var.get()) if hasattr(self, '_prompt_connect_var') else getattr(self._settings, 'prompt_for_connect_on_startup', True),
            auto_search_clipboard_after_connect=bool(self._auto_search_after_var.get()) if hasattr(self, '_auto_search_after_var') else getattr(self._settings, 'auto_search_clipboard_after_connect', False),
            auto_load_multi_skus_without_prompt=bool(self._auto_load_multi_var.get()) if hasattr(self, '_auto_load_multi_var') else getattr(self._settings, 'auto_load_multi_skus_without_prompt', False),
            open_root_on_sku_found=bool(self._open_root_var.get()) if hasattr(self, '_open_root_var') else getattr(self._settings, 'open_root_on_sku_found', False),
            recent_skus=self._settings.recent_skus,
            default_suffix=getattr(self._settings, 'default_suffix', ' - FTR '),
            show_help_on_startup=bool(self._show_welcome_var.get()) if hasattr(self, '_show_welcome_var') else getattr(self._settings, 'show_help_on_startup', True),
        )
        # If auto-connect is enabled, suppress future startup prompts automatically
        if updated.connect_on_startup:
            updated.prompt_for_connect_on_startup = False
        self._on_save(updated)
        self.destroy()

    def _clear_working_folder(self) -> None:
        """Clear the working folder field (persisted on Save)."""
        try:
            self._working_entry.configure(state='normal')
            self.working_var.set('')
            self._working_entry.configure(state='readonly')
        except Exception:
            pass

    # (update functionality intentionally removed for beta)



    def _format_account(self, account: str | None) -> str:
        return f'Account: {account or "(unauthenticated)"}'

    def set_account(self, account: str | None) -> None:
        """Update the account label live (called after successful connect/clear)."""
        try:
            self._current_account = account
            self._account_var.set(self._format_account(account))
        except Exception:
            pass

    def _center_on_parent_or_screen(self) -> None:
        try:
            self.update_idletasks()
            w = self.winfo_width() or self.winfo_reqwidth()
            h = self.winfo_height() or self.winfo_reqheight()
            m = self.master if isinstance(self.master, tk.Misc) else None
            if m is not None:
                try:
                    m.update_idletasks()
                except Exception:
                    pass
                mx = m.winfo_rootx()
                my = m.winfo_rooty()
                mw = m.winfo_width() or m.winfo_reqwidth()
                mh = m.winfo_height() or m.winfo_reqheight()
                x = mx + max((mw - w) // 2, 0)
                y = my + max((mh - h) // 2, 0)
            else:
                sw = self.winfo_screenwidth()
                sh = self.winfo_screenheight()
                x = max((sw - w) // 2, 0)
                y = max((sh - h) // 2, 0)
            self.geometry(f"{w}x{h}+{x}+{y}")
        except Exception:
            pass

    # (no reset welcome control)


# =================== END SETTINGS DIALOG ===================
