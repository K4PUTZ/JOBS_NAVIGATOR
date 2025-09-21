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
        # Favorites are disabled until a SKU is detected
        self._favorites_enabled: bool = False
        self._build_ui()
        # Bind favorite hotkeys once (handlers read from current settings)
        self._bind_favorite_hotkeys()

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

        # Current SKU field on the right side
        right_spacer = ttk.Frame(status_bar)
        right_spacer.pack(side='left', expand=True)
        ttk.Label(status_bar, text='Current SKU:').pack(side='left')
        self._current_sku_var = tk.StringVar(value='(none)')
        self._current_sku_label = ttk.Label(status_bar, textvariable=self._current_sku_var)
        self._current_sku_label.pack(side='left', padx=(6, 0))

        ttk.Label(sidebar, text='Favorites').pack(anchor='w')
        self._favorites_frame = ttk.Frame(sidebar)
        self._favorites_frame.pack(fill='x', pady=(2, 12))
        self._favorite_buttons: list[ttk.Button] = []
        self._render_favorites()

        ttk.Label(sidebar, text='Recent SKUs').pack(anchor='w')
        # Recent SKUs: up to 7 copy buttons with dark tooltips
        self._recents_rows = ttk.Frame(sidebar)
        self._recents_rows.pack(fill='x', pady=(2, 0))
        self._recent_buttons: list[ttk.Button] = []
        self._recent_tooltips: list[_Tooltip] = []
        self._recent_full_values: list[str] = [""] * 7
        for i in range(7):
            row = ttk.Frame(self._recents_rows)
            row.pack(fill='x', pady=1)
            btn = ttk.Button(row, text='⧉ (empty)', width=32, command=lambda idx=i: self._on_recent_click(idx))
            btn.pack(side='left', fill='x', expand=True)
            tip = _Tooltip(btn, text='No recent SKU', bg='#333333', fg='#ffffff')
            self._recent_buttons.append(btn)
            self._recent_tooltips.append(tip)

        # Initialize as empty/disabled
        self.update_recents([])

        self.pack(fill='both', expand=True)

    def _render_favorites(self) -> None:
        # Clear existing
        for child in list(self._favorites_frame.children.values()):
            try:
                child.destroy()
            except Exception:
                pass
        self._favorite_buttons.clear()
        # Rebuild with number labels 1..N
        for idx, favorite in enumerate(self._settings.favorites, start=1):
            row = ttk.Frame(self._favorites_frame)
            row.pack(fill='x', pady=2)
            num_lbl = tk.Label(row, text=f"{idx}.", width=3, anchor='e')
            num_lbl.pack(side='left', padx=(0, 4))
            label_text = favorite.label or '(empty)'
            btn = ttk.Button(row, text=label_text, command=lambda f=favorite: self._on_launch_shortcut(f.path))
            btn.pack(side='left', fill='x', expand=True)
            # Apply disabled state until a SKU is detected
            try:
                btn.configure(state=(tk.NORMAL if self._favorites_enabled else tk.DISABLED))
            except Exception:
                pass
            self._favorite_buttons.append(btn)

    def refresh_favorites(self, settings: Settings) -> None:
        self._settings = settings
        self._render_favorites()
        # No need to rebind hotkeys; handlers use current self._settings

    def set_favorites_enabled(self, enabled: bool) -> None:
        """Enable/disable all favorite buttons and update internal flag."""
        self._favorites_enabled = bool(enabled)
        for btn in getattr(self, '_favorite_buttons', []):
            try:
                btn.configure(state=(tk.NORMAL if self._favorites_enabled else tk.DISABLED))
            except Exception:
                pass

    def set_current_sku(self, sku: str | None) -> None:
        """Update the current SKU display in the status bar."""
        value = (sku or '').strip() or '(none)'
        try:
            self._current_sku_var.set(value)
        except Exception:
            pass

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
        """Populate the recent SKU buttons.

        Shows up to 7 items, numbered 1..7, each with a copy glyph and truncated label.
        Full SKU appears in a dark tooltip. Clicking copies the full SKU and shows a toast.
        """
        items = list(recents)[:7]
        # Fill slots
        for i in range(7):
            if i < len(items) and items[i]:
                full = str(items[i])
                self._recent_full_values[i] = full
                text = f"⧉ {self._format_recent_text(full)}"
                try:
                    self._recent_buttons[i].configure(text=text, state=tk.NORMAL)
                except Exception:
                    pass
                # Tooltip: dark theme
                try:
                    self._recent_tooltips[i].set_text(f"Click to copy\n{full}")
                    # Update colors (in case instance reused)
                    self._recent_tooltips[i].bg = '#333333'
                    self._recent_tooltips[i].fg = '#ffffff'
                except Exception:
                    pass
            else:
                self._recent_full_values[i] = ""
                try:
                    self._recent_buttons[i].configure(text='⧉ (empty)', state=tk.DISABLED)
                except Exception:
                    pass
                try:
                    self._recent_tooltips[i].set_text('No recent SKU')
                    self._recent_tooltips[i].bg = '#333333'
                    self._recent_tooltips[i].fg = '#ffffff'
                except Exception:
                    pass

    # =================== RECENTS INTERACTIONS ===================
    def _on_recent_click(self, index: int) -> None:
        try:
            full = self._recent_full_values[index]
        except Exception:
            full = ""
        if not full:
            return
        self._copy_to_clipboard(full)
        self.append_console(f"Copied SKU: {full}")
        # Show a small transient toast near the button
        try:
            btn = self._recent_buttons[index]
            self._show_toast(btn, 'Copied!', duration_ms=900)
        except Exception:
            pass

    def _copy_to_clipboard(self, text: str) -> None:
        try:
            self.clipboard_clear()
            self.clipboard_append(text)
            # Ensure clipboard is updated immediately
            self.update_idletasks()
        except Exception:
            try:
                import pyperclip  # type: ignore
                pyperclip.copy(text)
            except Exception:
                pass

    def _format_recent_text(self, sku: str, max_len: int = 28) -> str:
        s = str(sku)
        if len(s) <= max_len:
            return s
        return s[: max_len - 1] + '…'

    def _show_toast(self, widget: tk.Widget, text: str, *, duration_ms: int = 900) -> None:
        try:
            x = widget.winfo_rootx() + 10
            y = widget.winfo_rooty() - 10  # above the widget
            tw = tk.Toplevel(widget)
            tw.wm_overrideredirect(True)
            tw.wm_geometry(f"+{x}+{y}")
            lbl = tk.Label(tw, text=text, bg='#333333', fg='#ffffff', bd=0, padx=6, pady=3)
            lbl.pack()
            # Auto-destroy
            tw.after(max(200, duration_ms), tw.destroy)
        except Exception:
            pass

    # Hotkeys intentionally not bound; recents are mouse/touch only

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

    # =================== FAVORITES HOTKEYS ===================
    def _bind_favorite_hotkeys(self) -> None:
        """Bind Alt/Option + digit keys to launch favorites (1..9, 0=10)."""
        top = self.winfo_toplevel()

        def handler_for_index(i: int):
            def _h(event=None):  # noqa: ANN001
                try:
                    # Ignore hotkeys while favorites are disabled
                    if not self._favorites_enabled:
                        return
                    if 0 <= i < len(self._settings.favorites):
                        path = self._settings.favorites[i].path
                        if path:
                            self._on_launch_shortcut(path)
                except Exception:
                    pass
            return _h

        # Map 1..9 to 0..8, and 0 to index 9 (10th)
        indices = {str(d): (d - 1) for d in range(1, 10)}
        indices['0'] = 9
        for key, idx in indices.items():
            h = handler_for_index(idx)
            # Alt bindings
            try:
                top.bind_all(f'<Alt-Key-{key}>', h, add=True)
            except Exception:
                pass
            # macOS Option bindings
            try:
                top.bind_all(f'<Option-Key-{key}>', h, add=True)
            except Exception:
                pass


class _Tooltip:
    """Minimal tooltip helper for a Tk widget (supports custom colors)."""

    def __init__(self, widget: tk.Widget, *, text: str | None = None, bg: str = '#ffffe0', fg: str = '#000000'):
        self.widget = widget
        self.text = text or ''
        self.bg = bg
        self.fg = fg
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
            label = tk.Label(
                tw,
                name='tooltip_label',
                text=self.text,
                justify='left',
                background=self.bg,
                foreground=self.fg,
                relief='solid',
                borderwidth=1,
                font=('tahoma', '8', 'normal'),
            )
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
