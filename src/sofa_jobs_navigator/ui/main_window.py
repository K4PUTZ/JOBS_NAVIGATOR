"""Main window layout for Sofa Jobs Navigator."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable, Iterable

from ..config.settings import Settings
from ..config.flags import FLAGS


# =================== MAIN WINDOW ===================
# Builds the primary UI: status console, favorites list, recent SKUs, and controls.
# ---------------------------------------------------


class MainWindow(ttk.Frame):
    """Compose the root layout for the application."""

    def __init__(
        self,
        master: tk.Misc,
        *,
        settings: Settings,
        on_launch_shortcut: Callable[[str], None],
        on_open_settings: Callable[[], None],
    ) -> None:
        super().__init__(master, padding=12)
        self._settings = settings
        self._on_launch_shortcut = on_launch_shortcut
        self._on_open_settings = on_open_settings
        self._build_ui()

    # =================== UI CONSTRUCTION ===================
    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=3)
        self.columnconfigure(1, weight=1)
        # Make the middle row (console/sidebar) expand; status bar stays fixed at bottom
        self.rowconfigure(1, weight=1)

        console_frame = ttk.LabelFrame(self, text='Console')
        console_frame.grid(row=1, column=0, sticky='nsew', padx=(0, 12))
        console_frame.columnconfigure(0, weight=1)
        console_frame.rowconfigure(0, weight=1)
        self.console_text = tk.Text(console_frame, height=12, wrap='word', state='disabled')
        self.console_text.grid(row=0, column=0, sticky='nsew')

        sidebar = ttk.Frame(self)
        sidebar.grid(row=1, column=1, sticky='ns')
        settings_btn = ttk.Button(sidebar, text='Settings', command=self._on_open_settings)
        settings_btn.pack(fill='x', pady=(0, 8))

        # Status bar at the bottom
        status_bar = ttk.Frame(self)
        status_bar.grid(row=2, column=0, columnspan=2, sticky='ew', pady=(6, 0))
        ttk.Label(status_bar, text='Status:').pack(side='left')
        self._status_var = tk.StringVar(value='Offline')
        # Colored status label (green when online, gray when offline)
        self._status_label = ttk.Label(status_bar, textvariable=self._status_var)
        self._status_label.pack(side='left', padx=(6, 0))
        # Tooltip for additional details
        self._status_tooltip = _Tooltip(self._status_label)

        ttk.Label(sidebar, text='Favorites').pack(anchor='w')
        self._favorites_frame = ttk.Frame(sidebar)
        self._favorites_frame.pack(fill='x', pady=(2, 12))
        self._favorite_buttons: list[ttk.Button] = []
        self._render_favorites()

        ttk.Label(sidebar, text='Recent SKUs').pack(anchor='w')
        self._recents_var = tk.StringVar(value='(none)')
        ttk.Label(sidebar, textvariable=self._recents_var, justify='left').pack(fill='x', pady=(2, 0))

        self.pack(fill='both', expand=True)

    def _render_favorites(self) -> None:
        for btn in self._favorite_buttons:
            btn.destroy()
        self._favorite_buttons.clear()
        for favorite in self._settings.favorites:
            label = favorite.label or '(empty)'
            btn = ttk.Button(self._favorites_frame, text=label, command=lambda f=favorite: self._on_launch_shortcut(f.path))
            btn.pack(fill='x', pady=2)
            self._favorite_buttons.append(btn)

    def refresh_favorites(self, settings: Settings) -> None:
        self._settings = settings
        self._render_favorites()

    # =================== CONSOLE HELPERS ===================
    def append_console(self, message: str) -> None:
        self.console_text.configure(state='normal')
        self.console_text.insert('end', message + '\n')
        self.console_text.configure(state='disabled')
        self.console_text.see('end')
        # Mirror console to terminal when UI diagnostics or verbose logging are enabled
        try:
            if FLAGS.ui_debug or FLAGS.verbose_logging:
                print(message, flush=True)
        except Exception:
            pass

    def update_recents(self, recents: Iterable[str]) -> None:
        self._recents_var.set('\n'.join(recents) if recents else '(none)')

    # =================== STATUS HELPERS ===================
    def set_status(self, *, online: bool, account: str | None, token_expiry_iso: str | None = None) -> None:
        label = 'Online' if online else 'Offline'
        if account:
            label += f' · {account}'
        self._status_var.set(label)
        # Apply color via widget style map
        try:
            color = '#198754' if online else '#6c757d'  # Bootstrap-ish green/gray
            self._status_label.configure(foreground=color)
        except Exception:
            pass
        # Tooltip text
        tip = 'Connected' if online else 'Not connected'
        if token_expiry_iso:
            tip += f'\nToken expiry: {token_expiry_iso}'
        self._status_tooltip.set_text(tip)


class _Tooltip:
    """Minimal tooltip helper for a Tk widget."""

    def __init__(self, widget: tk.Widget, *, text: str | None = None):
        self.widget = widget
        self.text = text or ''
        self.tip_window: tk.Toplevel | None = None
        widget.bind('<Enter>', self._show)
        widget.bind('<Leave>', self._hide)

    def set_text(self, text: str) -> None:
        self.text = text
        # If currently showing, refresh contents
        if self.tip_window is not None:
            try:
                label = self.tip_window.children.get('tooltip_label')
                if isinstance(label, tk.Label):
                    label.configure(text=self.text)
            except Exception:
                pass

    def _show(self, event=None):  # noqa: ANN001
        if not self.text or self.tip_window is not None:
            return
        try:
            x = self.widget.winfo_rootx() + 10
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 8
            self.tip_window = tw = tk.Toplevel(self.widget)
            tw.wm_overrideredirect(True)
            tw.wm_geometry(f"+{x}+{y}")
            label = tk.Label(tw, name='tooltip_label', text=self.text, justify='left',
                             background='#ffffe0', relief='solid', borderwidth=1,
                             font=('tahoma', '8', 'normal'))
            label.pack(ipadx=4, ipady=2)
        except Exception:
            self.tip_window = None

    def _hide(self, event=None):  # noqa: ANN001
        if self.tip_window is not None:
            try:
                self.tip_window.destroy()
            except Exception:
                pass
            self.tip_window = None


# =================== END MAIN WINDOW ===================
