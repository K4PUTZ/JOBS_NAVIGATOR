"""Main window layout for Sofa Jobs Navigator."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from ..version import app_display_brand
from typing import Callable, Iterable
import re

from ..config.settings import Settings
from ..config.flags import FLAGS
from ..logging.console_file import CONSOLE_FILE_LOGGER, open_console_log_file


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
        on_check_clipboard: Callable[[], None] | None = None,
        on_search: Callable[[], None] | None = None,
        on_about: Callable[[], None] | None = None,
        on_help: Callable[[], None] | None = None,
        on_create_sku_folder: Callable[[str], None] | None = None,
        on_settings_change: Callable[[Settings], None] | None = None,
        on_clear_recents: Callable[[], None] | None = None,
        on_auth_connect: Callable[[], None] | None = None,
        on_auth_clear: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(master, padding=12)
        self._settings = settings
        self._on_settings_change = on_settings_change
        self._on_launch_shortcut = on_launch_shortcut
        self._on_open_settings = on_open_settings
        self._on_check_clipboard = on_check_clipboard
        self._on_search = on_search
        self._on_about = on_about
        self._on_help = on_help
        self._on_create_sku_folder = on_create_sku_folder
        self._on_clear_recents = on_clear_recents
        # Optional auth menu handlers (provided by app)
        self._on_auth_connect = on_auth_connect
        self._on_auth_clear = on_auth_clear
        self._menu_recents: tk.Menu | None = None
        # Favorites are disabled until a SKU is detected
        self._favorites_enabled = False
        self._build_ui()
        # Bind favorite hotkeys once (handlers read from current settings)
        self._bind_favorite_hotkeys()
        # Bind number keys to recents 1..7
        self._bind_recent_hotkeys()
        # Build application menu and bind accelerators
        try:
            self._build_menu()
        except Exception:
            pass

    # =================== UI CONSTRUCTION ===================
    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=3)
        self.columnconfigure(1, weight=1)
        # Make the content row (console/sidebar) expand; status bar stays fixed at bottom.
        # Row indices after adding a toolbar + spacer + separator + spacer + spacer:
        #   0: toolbar, 1: spacer, 2: separator, 3: spacer, 4: spacer, 5: console/sidebar, 6: status bar
        self.rowconfigure(5, weight=1)

        # Style: keep only the yellow accent for the current SKU value in the status bar
        try:
            style = ttk.Style(self)
            # Ensure disabled label text appears gray across the app
            try:
                style.map('TLabel', foreground=[('disabled', '#6c757d')])
            except Exception:
                pass
            # Ensure disabled button text appears dark gray
            try:
                style.map('TButton', foreground=[('disabled', '#6c757d')])
            except Exception:
                pass
            style.configure('Sofa.SKU.TLabel', foreground='#ffc107')
            # Custom style for enabled favorite buttons with cyan text
            style.configure('Sofa.Favorite.TButton', foreground='#0dcaf0')
        except Exception:
            pass

        # Toolbar area (row 0)
        self._build_toolbar(row=0)

        # Spacer empty line (row 1)
        ttk.Frame(self, height=6).grid(row=1, column=0, columnspan=2, sticky='ew')

        # Separator (row 2)
        ttk.Separator(self, orient='horizontal').grid(row=2, column=0, columnspan=2, sticky='ew', pady=(0, 0))

        # Spacer empty line after separator (row 3)
        ttk.Frame(self, height=6).grid(row=3, column=0, columnspan=2, sticky='ew')
        # Second spacer line after separator (row 4)
        ttk.Frame(self, height=6).grid(row=4, column=0, columnspan=2, sticky='ew')

        # Console (row 5, col 0)
        console_frame = ttk.LabelFrame(self, text='Console')
        console_frame.grid(row=5, column=0, sticky='nsew', padx=(0, 12))
        console_frame.columnconfigure(0, weight=1)
        console_frame.rowconfigure(0, weight=1)
        # Attach vertical scroll bar so long console sessions remain accessible
        self._console_scroll_y = ttk.Scrollbar(console_frame, orient='vertical')
        self._console_scroll_y.grid(row=0, column=1, sticky='ns')
        self.console_text = tk.Text(
            console_frame,
            height=12,
            wrap='word',
            state='disabled',
            yscrollcommand=self._console_scroll_y.set,
        )
        self.console_text.grid(row=0, column=0, sticky='nsew')
        self._console_scroll_y.configure(command=self.console_text.yview)
        # Spacer and action buttons beneath the console log
        try:
            ttk.Frame(console_frame, height=4).grid(row=1, column=0, columnspan=2, sticky='ew')
        except Exception:
            pass
        button_row = ttk.Frame(console_frame)
        button_row.grid(row=2, column=0, columnspan=2, sticky='ew', pady=(4, 2))
        button_row.columnconfigure(0, weight=1)
        try:
            ttk.Frame(button_row).grid(row=0, column=0, sticky='ew')
        except Exception:
            pass
        self._clear_console_btn = ttk.Button(button_row, text='Clear Console', command=self._clear_console)
        self._clear_console_btn.grid(row=0, column=1, padx=(0, 6))
        self._open_log_btn = ttk.Button(button_row, text='Log', command=self._open_console_log)
        self._open_log_btn.grid(row=0, column=2)
        # Default console colors: white text on dark background; caret visible
        try:
            self.console_text.configure(bg='#1e1e1e', fg='#ffffff', insertbackground='#ffffff')
        except Exception:
            pass
        # Context menu: right-click to Copy selection
        try:
            self._console_menu = tk.Menu(self, tearoff=0)
            self._console_menu.add_command(label='Copy', command=self._copy_console_selection)
            self._console_menu.add_command(label='Clear Console', command=self._clear_console)
            # Right-click bindings (Windows/Linux) and Ctrl-click (macOS)
            self.console_text.bind('<Button-3>', self._show_console_context_menu, add=True)
            self.console_text.bind('<Button-2>', self._show_console_context_menu, add=True)
            self.console_text.bind('<Control-Button-1>', self._show_console_context_menu, add=True)
        except Exception:
            self._console_menu = None  # type: ignore[assignment]
        # Console color tags for categorized messages
        try:
            self.console_text.tag_configure('error', foreground='#dc3545')      # red
            self.console_text.tag_configure('warning', foreground='#ffc107')    # gold yellow
            self.console_text.tag_configure('success', foreground='#90ee90')    # light green
            self.console_text.tag_configure('hint', foreground='#ff69b4')       # pink
            self.console_text.tag_configure('sku', foreground='#0dcaf0')        # cyan for SKU values
        except Exception:
            pass

        # Sidebar (row 5, col 1)
        sidebar = ttk.Frame(self)
        sidebar.grid(row=5, column=1, sticky='ns')

        # Sidebar: CURRENT SKU section above Favorites
        try:
            # Two empty lines
            ttk.Frame(sidebar, height=6).pack(fill='x')
            ttk.Frame(sidebar, height=6).pack(fill='x')
            # Label
            ttk.Label(sidebar, text='CURRENT SKU').pack(anchor='w')
            # Field container
            field_row = ttk.Frame(sidebar)
            field_row.pack(fill='x', pady=(2, 2))
            # Read-only field: bold cyan on dark gray, truncated at end
            self._side_current_sku_var = tk.StringVar(value='(none)')
            self._side_current_sku_entry = tk.Entry(
                field_row,
                textvariable=self._side_current_sku_var,
                font=('Segoe UI', 10, 'bold'),
                bg='#2b2b2b',
                fg='#0dcaf0',
                disabledforeground='#0dcaf0',
                disabledbackground='#2b2b2b',
                relief='flat',
                width=34,
            )
            self._side_current_sku_entry.pack(fill='x')
            try:
                self._side_current_sku_entry.configure(state='disabled')  # make read-only
            except Exception:
                pass
            # Tooltip with full SKU (dark theme)
            self._side_current_sku_tooltip = _Tooltip(self._side_current_sku_entry, text='(none)', bg='#333333', fg='#ffffff')
            # Two empty lines after
            ttk.Frame(sidebar, height=6).pack(fill='x')
            ttk.Frame(sidebar, height=6).pack(fill='x')
        except Exception:
            pass

        # Status bar at the bottom (row 6) — split into two rows
        status_bar = ttk.Frame(self)
        status_bar.grid(row=6, column=0, columnspan=2, sticky='ew', pady=(6, 0))

        # Visual separation at the top of the status bar
        try:
            # Two empty lines above
            ttk.Frame(status_bar, height=6).pack(fill='x')
            ttk.Frame(status_bar, height=6).pack(fill='x')
            # Separator
            ttk.Separator(status_bar, orient='horizontal').pack(fill='x')
            # Two empty lines below
            ttk.Frame(status_bar, height=6).pack(fill='x')
            ttk.Frame(status_bar, height=6).pack(fill='x')
        except Exception:
            pass

        # Row 1: Connection Status (left) + Current SKU (right)
        row1 = ttk.Frame(status_bar)
        row1.pack(fill='x')
        left1 = ttk.Frame(row1)
        left1.pack(side='left')
        ttk.Label(left1, text='Status:').pack(side='left')
        self._status_var = tk.StringVar(value='Offline')
        # Colored status label (green when online, gray when offline)
        self._status_label = ttk.Label(left1, textvariable=self._status_var)
        self._status_label.pack(side='left', padx=(6, 0))
        # Tooltip for additional details
        self._status_tooltip = _Tooltip(self._status_label)
    # (Removed Current SKU from status bar)

        # Row 2: Working Folder (left) + Create Folder controls (right)
        row2 = ttk.Frame(status_bar)
        row2.pack(fill='x', pady=(4, 0))
        left2 = ttk.Frame(row2)
        left2.pack(side='left')
        ttk.Label(left2, text='Working Folder:').pack(side='left')
        self._working_folder_var = tk.StringVar(value='(none)')
        self._working_folder_label = ttk.Label(left2, textvariable=self._working_folder_var)
        self._working_folder_label.pack(side='left', padx=(6, 0))
        # Cyan addon: "/SKU + suffix" (shown when both folder and SKU exist)
        self._working_folder_sku_label = ttk.Label(left2, text='', foreground='#0dcaf0')
        self._working_folder_sku_label.pack(side='left', padx=(6, 0))
        # Spacer between left and right clusters
        ttk.Frame(row2).pack(side='left', expand=True)
        right2 = ttk.Frame(row2)
        right2.pack(side='left')
        # Suffix first
        ttk.Label(right2, text='Suffix').pack(side='left', padx=(8, 6))
        # Initialize suffix from settings (persisted)
        self._suffix_var = tk.StringVar(value=getattr(self._settings, 'default_suffix', ' - FTR '))
        self._suffix_entry = ttk.Entry(right2, textvariable=self._suffix_var, width=12)
        self._suffix_entry.pack(side='left')
        # Persist suffix when focus leaves the field
        try:
            self._suffix_entry.bind('<FocusOut>', lambda e: self._persist_suffix())
        except Exception:
            pass
        # Button after suffix
        self._create_btn = ttk.Button(right2, text='Create Folder', command=self._on_click_create_sku_folder)
        self._create_btn.pack(side='left', padx=(8, 0))
        # Disabled by default; will enable when a SKU is set and Working Folder configured
        try:
            self._create_btn.configure(state=tk.DISABLED)
        except Exception:
            pass
        # Tooltip explaining requirements
        try:
            self._create_btn_tooltip = _Tooltip(
                self._create_btn,
                text='Disabled: detect a SKU and set a Working Folder in Settings',
                bg='#333333',
                fg='#ffffff',
            )
        except Exception:
            self._create_btn_tooltip = None  # type: ignore[assignment]
        # Keep the cyan addon in sync if user edits suffix
        try:
            self._suffix_var.trace_add('write', lambda *args: self._refresh_working_folder_addon())
        except Exception:
            pass

        ttk.Label(sidebar, text='Favorites').pack(anchor='w')
        self._favorites_frame = ttk.Frame(sidebar)
        # Use grid inside favorites so labels/buttons align across rows
        self._favorites_frame.pack(fill='x', pady=(2, 12))
        try:
            self._favorites_frame.grid_columnconfigure(0, weight=0)
            self._favorites_frame.grid_columnconfigure(1, weight=1, uniform='fav')
        except Exception:
            pass
        self._favorite_buttons: list[ttk.Button] = []
        self._favorite_tooltips: list[_Tooltip] = []
        self._render_favorites()

        # Recent SKUs header with Clear button
        recents_header = ttk.Frame(sidebar)
        recents_header.pack(fill='x', anchor='w')
        ttk.Label(recents_header, text='Recent SKUs').pack(side='left', anchor='w')
        ttk.Button(
            recents_header, 
            text='Clear', 
            command=self._on_clear_recents_click,
            width=6
        ).pack(side='right', anchor='e')
        # Recent SKUs: up to 7 copy buttons with dark tooltips
        self._recents_rows = ttk.Frame(sidebar)
        # Use grid inside recents so labels/buttons align across rows
        self._recents_rows.pack(fill='x', pady=(2, 0))
        try:
            self._recents_rows.grid_columnconfigure(0, weight=0)
            self._recents_rows.grid_columnconfigure(1, weight=1, uniform='rec')
        except Exception:
            pass
        self._recent_buttons: list[ttk.Button] = []
        self._recent_tooltips: list[_Tooltip] = []
        self._recent_full_values: list[str] = [""] * 7
        for i in range(7):
            # Index label like (1), (2), ... (fixed width, right-aligned)
            idx_lbl = ttk.Label(self._recents_rows, text=f"({i+1})", width=4, anchor='e')
            idx_lbl.grid(row=i, column=0, sticky='e', padx=(0, 6), pady=(1, 1))
            # Button expands to fill column 1; all buttons share width via grid
            btn = ttk.Button(self._recents_rows, text='⧉ (empty)', command=lambda idx=i: self._on_recent_click(idx))
            btn.grid(row=i, column=1, sticky='ew', pady=(1, 1))
            tip = _Tooltip(btn, text='No recent SKU', bg='#333333', fg='#ffffff')
            self._recent_buttons.append(btn)
            self._recent_tooltips.append(tip)

        # Initialize as empty/disabled
        self.update_recents([])

        # Clicking anywhere outside console or suffix entry will clear their selection
        try:
            self._install_global_deselect_handlers()
        except Exception:
            pass

        self.pack(fill='both', expand=True)

    # -------------------- Toolbar --------------------
    def _build_toolbar(self, *, row: int = 0) -> None:
        bar = ttk.Frame(self)
        bar.grid(row=row, column=0, columnspan=2, sticky='ew')
        bar.columnconfigure(0, weight=1)
        bar.columnconfigure(1, weight=0)

        # Left branding: colored squares (logo) + app name and version
        brand = ttk.Frame(bar)
        brand.grid(row=0, column=0, sticky='nw', padx=(5, 0))
        try:
            # Row 0: squares aligned at the top-left, touching
            row0 = ttk.Frame(brand)
            row0.pack(side='top', anchor='w')
            colors = ['#ffd400', '#00e5ff', '#39ff14', '#ff00ff', '#ff3b30', '#007aff']
            for c in colors:
                sq = tk.Frame(row0, width=12, height=12, background=c, highlightthickness=0, bd=0)
                sq.pack(side='left', padx=0)
        except Exception:
            pass
        # Spacer lines between squares and program name
        ttk.Frame(brand, height=4).pack(side='top', anchor='w')
        ttk.Frame(brand, height=4).pack(side='top', anchor='w')
        # Row 1: program name below squares, with registered mark
        ttk.Label(brand, text=app_display_brand()).pack(side='top', anchor='w')

        # Right tools: align buttons to the right
        tools = ttk.Frame(bar)
        tools.grid(row=0, column=1, sticky='e')
        # Create tool buttons with vector-like glyph (font chars) + caption + keybinding
        # Welcome (Home) first
        self._make_tool_button(tools, icon='💡', label='Welcome', key='Home', command=self._on_tool_help)
        # Check Clipboard (F9)
        self._make_tool_button(tools, icon='📋', label='Check Clipboard', key='F9', command=self._on_tool_check_clipboard)
        # 2) About (F10)
        self._make_tool_button(tools, icon='ℹ️', label='About', key='F10', command=self._on_tool_about)
        # 3) Settings (F11)
        self._make_tool_button(tools, icon='⚙️', label='Settings', key='F11', command=self._on_tool_settings)
        # 4) Search SKU (F12)
        self._make_tool_button(tools, icon='🔍', label='Search SKU', key='F12', command=self._on_tool_search)

    def _make_tool_button(self, parent: tk.Misc, *, icon: str, label: str, key: str, command: Callable[[], None]) -> None:
        # A vertically-stacked button: icon (big), label (small), keybinding hint (small)
        outer = ttk.Frame(parent, padding=(4, 2))
        outer.pack(side='left', padx=(0, 8))
        # Using Labels to mimic vector icon button style, clickable via binding
        icon_lbl = ttk.Label(outer, text=icon, font=('Segoe UI Emoji', 18))
        icon_lbl.pack()
        name_lbl = ttk.Label(outer, text=label)
        name_lbl.pack()
        key_lbl = ttk.Label(outer, text=f'({key})', foreground='#6c757d')
        key_lbl.pack()
        # Bind click/Enter on entire outer frame
        for w in (outer, icon_lbl, name_lbl, key_lbl):
            w.bind('<Button-1>', lambda e, c=command: c())
            w.bind('<Return>', lambda e, c=command: c())
        # Add a simple hover style effect (optional)
        def on_enter(_e):
            try:
                outer.configure(style='')
            except Exception:
                pass
        def on_leave(_e):
            try:
                outer.configure(style='')
            except Exception:
                pass
        outer.bind('<Enter>', on_enter)
        outer.bind('<Leave>', on_leave)

    # -------------------- Application Menu --------------------
    def _build_menu(self) -> None:
        """Create a standard menubar with application actions, favorites, recents, auth and help."""
        top = self.winfo_toplevel()
        try:
            menubar = tk.Menu(top)
            # File menu
            file_menu = tk.Menu(menubar, tearoff=0)
            file_menu.add_command(label='Exit', command=top.quit, accelerator='Ctrl+Q')
            menubar.add_cascade(label='File', menu=file_menu)

            # Actions menu
            actions = tk.Menu(menubar, tearoff=0)
            actions.add_command(label='Search SKU', command=self._on_tool_search, accelerator='F12')
            actions.add_command(label='Check Clipboard', command=self._on_tool_check_clipboard, accelerator='F9')
            actions.add_command(label='Create SKU Folder', command=self._on_click_create_sku_folder)
            menubar.add_cascade(label='Actions', menu=actions)

            # Favorites menu (mirror favorites with F1..F8)
            fav_menu = tk.Menu(menubar, tearoff=0)
            for idx, fav in enumerate(getattr(self._settings, 'favorites', [])[:8]):
                display = fav.label or f'Favorite {idx+1}'
                key = f'F{idx+1}'
                def _make_cmd(p):
                    return lambda p=p: self._on_launch_shortcut(p)
                fav_menu.add_command(label=display, command=_make_cmd(fav.path), accelerator=key)
            menubar.add_cascade(label='Favorites', menu=fav_menu)

            # Recents menu (1..7)
            rec_menu = tk.Menu(menubar, tearoff=0)
            self._menu_recents = rec_menu
            self._refresh_menu_recents()
            menubar.add_cascade(label='Recents', menu=rec_menu)

            # Auth menu
            auth_menu = tk.Menu(menubar, tearoff=0)
            auth_menu.add_command(label='Connect to Google Drive', command=(self._on_auth_connect if callable(getattr(self, '_on_auth_connect', None)) else (lambda: None)), accelerator='Ctrl+K')
            auth_menu.add_command(label='Clear Credentials', command=(self._on_auth_clear if callable(getattr(self, '_on_auth_clear', None)) else (lambda: None)), accelerator='Ctrl+L')
            menubar.add_cascade(label='Auth', menu=auth_menu)

            # Help menu
            help_menu = tk.Menu(menubar, tearoff=0)
            help_menu.add_command(label='Welcome', command=self._on_tool_help, accelerator='Home')
            help_menu.add_command(label='About', command=self._on_tool_about, accelerator='F10')
            help_menu.add_command(label='Settings', command=self._on_tool_settings, accelerator='F11')
            menubar.add_cascade(label='Help', menu=help_menu)

            try:
                top.config(menu=menubar)
            except Exception:
                pass

            # Bind accelerators to the same callbacks for robustness
            try:
                top.bind_all('<F12>', lambda e: self._on_tool_search(), add=True)
                top.bind_all('<F9>', lambda e: self._on_tool_check_clipboard(), add=True)
                top.bind_all('<F10>', lambda e: self._on_tool_about(), add=True)
                top.bind_all('<F11>', lambda e: self._on_tool_settings(), add=True)
                top.bind_all('<Home>', lambda e: self._on_tool_help(), add=True)
                top.bind_all('<Control-q>', lambda e: top.quit(), add=True)
                top.bind_all('<Control-k>', lambda e: (self._on_auth_connect() if callable(getattr(self, '_on_auth_connect', None)) else None), add=True)
                top.bind_all('<Control-l>', lambda e: (self._on_auth_clear() if callable(getattr(self, '_on_auth_clear', None)) else None), add=True)
            except Exception:
                pass
        except Exception:
            pass

    # -------------------- Toolbar Actions --------------------
    def _on_tool_search(self) -> None:
        # Search SKU: delegate to app callback if provided; otherwise hint
        try:
            if callable(self._on_search):
                self._on_search()  # type: ignore[misc]
                return
        except Exception:
            pass
        self.console_hint('Search SKU: copy a SKU and press F12 (toolbar will invoke when wired).')

    def _on_tool_settings(self) -> None:
        try:
            self._on_open_settings()
        except Exception:
            pass

    def _on_tool_about(self) -> None:
        # Placeholder: will implement later; allow app to override
        try:
            if callable(self._on_about):
                self._on_about()  # type: ignore[misc]
                return
        except Exception:
            pass
        # About dialog failed - no message needed

    def _on_tool_help(self) -> None:
        try:
            if callable(self._on_help):
                self._on_help()  # type: ignore[misc]
                return
        except Exception:
            pass
        # Help dialog failed - no message needed

    def _on_tool_check_clipboard(self) -> None:
        # Delegate to app to inspect clipboard and print to terminal
        try:
            if callable(self._on_check_clipboard):
                self._on_check_clipboard()  # type: ignore[misc]
                return
        except Exception:
            pass
        self.console_neutral('Checking clipboard for SKU… (F9)')

    def _render_favorites(self) -> None:
        # Clear existing
        for child in list(self._favorites_frame.children.values()):
            try:
                child.destroy()
            except Exception:
                pass
        self._favorite_buttons.clear()
        self._favorite_tooltips.clear()
        # Ensure grid columns are configured (idempotent)
        try:
            self._favorites_frame.grid_columnconfigure(0, weight=0)
            self._favorites_frame.grid_columnconfigure(1, weight=1, uniform='fav')
        except Exception:
            pass
        # Rebuild with number labels 1..N using grid for consistent alignment
        for r, favorite in enumerate(self._settings.favorites):
            idx = r + 1
            # Add an F-key hint label for the first 8 favorites
            hint_text = f"F{idx}" if idx <= 8 else ""
            hint = ttk.Label(self._favorites_frame, text=hint_text, width=4, anchor='e')
            hint.grid(row=r, column=0, sticky='e', padx=(0, 6), pady=(1, 1))
            label_text = favorite.label or '(empty)'
            btn = ttk.Button(self._favorites_frame, text=label_text, command=lambda f=favorite: self._on_launch_shortcut(f.path))
            btn.grid(row=r, column=1, sticky='ew', pady=(1, 1))
            
            # Create tooltip for the button
            tooltip_text = 'Search any SKU to enable the shortcuts.'
            if favorite.label or favorite.path:
                # This favorite is configured - tooltip depends on enabled state
                if self._favorites_enabled:
                    tooltip_text = f"Navigate to: {favorite.path or '(root)'}"
                else:
                    tooltip_text = 'Search any SKU to enable the shortcuts.'
            tip = _Tooltip(btn, text=tooltip_text, bg='#333333', fg='#ffffff')
            self._favorite_tooltips.append(tip)
            
            # Apply disabled state and style
            try:
                # Disable if the favorite is not configured at all (no label and no path)
                if not (favorite.label or favorite.path):
                    btn.configure(state=tk.DISABLED)
                else:
                    is_enabled = self._favorites_enabled
                    btn.configure(state=(tk.NORMAL if is_enabled else tk.DISABLED))
                    # Apply cyan style for enabled favorites
                    if is_enabled:
                        btn.configure(style='Sofa.Favorite.TButton')
                    else:
                        btn.configure(style='TButton')  # Reset to default style
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
        for idx, btn in enumerate(getattr(self, '_favorite_buttons', [])):
            try:
                fav = self._settings.favorites[idx] if idx < len(self._settings.favorites) else None
                if fav and not (getattr(fav, 'label', None) or getattr(fav, 'path', None)):
                    # Favorite not configured - always disabled
                    btn.configure(state=tk.DISABLED, style='TButton')
                else:
                    # Favorite is configured - enable/disable based on SKU detection
                    is_enabled = self._favorites_enabled
                    btn.configure(state=(tk.NORMAL if is_enabled else tk.DISABLED))
                    # Apply cyan style for enabled favorites
                    if is_enabled:
                        btn.configure(style='Sofa.Favorite.TButton')
                    else:
                        btn.configure(style='TButton')  # Reset to default style
                
                # Update tooltip text
                if idx < len(getattr(self, '_favorite_tooltips', [])):
                    tooltip = self._favorite_tooltips[idx]
                    if fav and (getattr(fav, 'label', None) or getattr(fav, 'path', None)):
                        # This favorite is configured - tooltip depends on enabled state
                        if self._favorites_enabled:
                            tooltip.set_text(f"Navigate to: {getattr(fav, 'path', None) or '(root)'}")
                        else:
                            tooltip.set_text('Search any SKU to enable the shortcuts.')
                    else:
                        # Favorite not configured - always show enable message
                        tooltip.set_text('Search any SKU to enable the shortcuts.')
            except Exception:
                pass

    def set_current_sku(self, sku: str | None) -> None:
        """Update the current SKU display in the status bar."""
        value = (sku or '').strip() or '(none)'
        # Update sidebar CURRENT SKU field (truncated) and tooltip
        try:
            short = self._format_recent_text(value, max_len=34)
            # Temporarily enable to update text if necessary
            try:
                self._side_current_sku_entry.configure(state='normal')
            except Exception:
                pass
            try:
                self._side_current_sku_var.set(short)
            except Exception:
                pass
            try:
                self._side_current_sku_entry.configure(state='disabled')
            except Exception:
                pass
            try:
                self._side_current_sku_tooltip.set_text(value)
                self._side_current_sku_tooltip.bg = '#333333'
                self._side_current_sku_tooltip.fg = '#ffffff'
            except Exception:
                pass
        except Exception:
            pass
        # Track current SKU (raw) and refresh addon
        try:
            self._current_sku_value = None if value == '(none)' else value
        except Exception:
            self._current_sku_value = None
        self._refresh_working_folder_addon()
        self._refresh_create_button_state()

    def get_current_sku(self) -> str | None:
        """Return the current SKU string or None when not set."""
        try:
            v = (getattr(self, '_current_sku_value', None) or '').strip()
            return v or None
        except Exception:
            return None

    # Working folder helpers
    def set_working_folder(self, folder: str | None) -> None:
        value = (folder or '').strip() or '(none)'
        try:
            self._working_folder_var.set(value)
        except Exception:
            pass
        self._refresh_working_folder_addon()
        self._refresh_create_button_state()

    def get_working_folder(self) -> str:
        try:
            return self._working_folder_var.get()
        except Exception:
            return '(none)'

    def get_suffix_text(self) -> str:
        try:
            return self._suffix_var.get()
        except Exception:
            return ''

    def _persist_suffix(self) -> None:
        """Persist current suffix into settings and update button tooltip/addon."""
        try:
            current = (self._suffix_var.get() or '')
        except Exception:
            current = ''
        try:
            # Update settings object in memory so Settings dialog save or app-initiated saves persist it
            if hasattr(self, '_settings'):
                setattr(self._settings, 'default_suffix', current)
        except Exception:
            pass
        # Notify app to persist settings immediately if callback provided
        try:
            if callable(getattr(self, '_on_settings_change', None)):
                self._on_settings_change(self._settings)  # type: ignore[misc]
        except Exception:
            pass
        # Refresh UI bits that depend on suffix
        self._refresh_working_folder_addon()
        self._refresh_create_button_state()

    def _refresh_working_folder_addon(self) -> None:
        """Show or hide the cyan "/SKU + suffix" addon after the working folder path.

        Conditions: shows only when a non-empty working folder and a current SKU are available.
        """
        try:
            folder = (self._working_folder_var.get() or '').strip()
        except Exception:
            folder = ''
        sku = (getattr(self, '_current_sku_value', None) or '').strip()
        if not folder or folder == '(none)' or not sku:
            try:
                self._working_folder_sku_label.configure(text='')
            except Exception:
                pass
            return
        # Build addon: "/SKU + suffix"
        try:
            suffix = self.get_suffix_text()
        except Exception:
            suffix = ''
        addon = f" /{sku}{suffix}"
        try:
            self._working_folder_sku_label.configure(text=addon)
        except Exception:
            pass

    def _refresh_create_button_state(self) -> None:
        """Enable the Create Folder button only when both SKU and Working Folder are set."""
        try:
            folder = (self._working_folder_var.get() or '').strip()
        except Exception:
            folder = ''
        try:
            sku = (getattr(self, '_current_sku_value', None) or '').strip()
        except Exception:
            sku = ''
        enabled = bool(sku) and bool(folder) and folder != '(none)'
        try:
            self._create_btn.configure(state=(tk.NORMAL if enabled else tk.DISABLED))
        except Exception:
            pass
        # Update tooltip to reflect current state and action
        try:
            if getattr(self, '_create_btn_tooltip', None) is not None:
                if enabled:
                    suffix = self.get_suffix_text()
                    self._create_btn_tooltip.set_text(f"Create local folder: {sku}{suffix}")
                    self._create_btn_tooltip.bg = '#333333'
                    self._create_btn_tooltip.fg = '#ffffff'
                else:
                    self._create_btn_tooltip.set_text('Disabled: detect a SKU and set a Working Folder in Settings')
                    self._create_btn_tooltip.bg = '#333333'
                    self._create_btn_tooltip.fg = '#ffffff'
        except Exception:
            pass

    # =================== CONSOLE HELPERS ===================
    def append_console(self, message: str, tag: str | None = None) -> None:
        """Append a line to the console with optional color tag."""
        self.console_text.configure(state='normal')
        start_index = self.console_text.index('end-1c')
        self.console_text.insert('end', message + '\n')
        end_index = self.console_text.index('end-1c')
        # Apply color tag if provided
        if tag:
            try:
                self.console_text.tag_add(tag, start_index, end_index)
            except Exception:
                pass
        self.console_text.configure(state='disabled')
        self.console_text.see('end')
        # Mirror console to terminal when UI diagnostics or verbose logging are enabled
        try:
            if FLAGS.ui_debug or FLAGS.verbose_logging:
                print(message, flush=True)
        except Exception:
            pass

    def append_console_highlight(self, message: str, *, highlight: str, highlight_tag: str = 'sku', line_tag: str | None = None) -> None:
        """Append a line and highlight SKU values in cyan."""
        self.console_text.configure(state='normal')
        line_start = self.console_text.index('end-1c')
        self.console_text.insert('end', message + '\n')
        line_end = self.console_text.index('end-1c')
        try:
            if line_tag:
                self.console_text.tag_add(line_tag, line_start, line_end)
            # Highlight the SKU value in cyan
            idx = self.console_text.search(highlight, line_start, stopindex=line_end, nocase=False)
            if idx:
                try:
                    end_idx = f"{idx}+{len(highlight)}c"
                    self.console_text.tag_add(highlight_tag, idx, end_idx)
                except Exception:
                    pass
        except Exception:
            pass
        self.console_text.configure(state='disabled')
        self.console_text.see('end')

    # Convenience wrappers with color categories
    def console_success(self, message: str) -> None:
        self.append_console(message, 'success')

    def console_warning(self, message: str) -> None:
        self.append_console(message, 'warning')

    def console_error(self, message: str) -> None:
        self.append_console(message, 'error')
        try:
            CONSOLE_FILE_LOGGER.log_error(message)
        except Exception:
            pass

    def console_sku_detected(self, sku: str) -> None:
        self.append_console_highlight(f'SKU detected: {sku}', highlight=sku, highlight_tag='sku')
        try:
            CONSOLE_FILE_LOGGER.log_sku(sku)
        except Exception:
            pass

    def console_hint(self, message: str) -> None:
        self.append_console(message, 'hint')

    def console_neutral(self, message: str) -> None:
        """White text for neutral messages."""
        self.append_console(message)

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

        self._refresh_menu_recents()

    # =================== RECENTS INTERACTIONS ===================
    def _refresh_menu_recents(self) -> None:
        menu = getattr(self, '_menu_recents', None)
        if menu is None:
            return
        try:
            menu.delete(0, 'end')
        except Exception:
            return
        values = getattr(self, '_recent_full_values', [])
        if not values:
            menu.add_command(label='(no recent SKUs)', state=tk.DISABLED)
            return
        for idx, value in enumerate(values, start=1):
            if value:
                label = f"{idx}. {value}"
                cmd = lambda i=idx - 1: self._on_recent_click(i)
                menu.add_command(label=label, command=cmd, accelerator=str(idx) if idx <= 9 else '')
            else:
                menu.add_command(label=f"{idx}. (empty)", state=tk.DISABLED)

    def _on_recent_click(self, index: int) -> None:
        try:
            full = self._recent_full_values[index]
        except Exception:
            full = ""
        if not full:
            return
        self._copy_to_clipboard(full)
        try:
            self.append_console_highlight(f"Copied SKU: {full}", highlight=full, highlight_tag='sku', line_tag='success')
        except Exception:
            self.append_console_highlight(f"Copied SKU: {full}", highlight=full, highlight_tag='sku')
        # Show a small transient toast near the button
        try:
            btn = self._recent_buttons[index]
            self._show_toast(btn, 'Copied!', duration_ms=900)
        except Exception:
            pass

    def _on_clear_recents_click(self) -> None:
        """Handle clicking the Clear button for recent SKUs."""
        if callable(self._on_clear_recents):
            try:
                self._on_clear_recents()
                self.console_neutral('Recent SKUs cleared.')
            except Exception as e:
                self.append_console(f'Failed to clear recent SKUs: {e}')

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

    def _show_console_context_menu(self, event):  # noqa: ANN001
        try:
            # Enable/disable Copy based on selection presence
            has_sel = False
            try:
                self.console_text.index('sel.first')
                self.console_text.index('sel.last')
                has_sel = True
            except Exception:
                has_sel = False
            try:
                self._console_menu.entryconfig(0, state=(tk.NORMAL if has_sel else tk.DISABLED))
            except Exception:
                pass
            try:
                # Clear Console should always be enabled, but guard in case menu missing
                self._console_menu.entryconfig(1, state=tk.NORMAL)
            except Exception:
                pass
            # Show the menu at cursor position
            self._console_menu.tk_popup(event.x_root, event.y_root)
        except Exception:
            pass
        finally:
            try:
                self._console_menu.grab_release()
            except Exception:
                pass
        return 'break'

    def _copy_console_selection(self) -> None:
        """Copy current selection from console to clipboard and show a small toast."""
        try:
            start = self.console_text.index('sel.first')
            end = self.console_text.index('sel.last')
        except Exception:
            return
        try:
            text = self.console_text.get(start, end)
        except Exception:
            text = ''
        if not text:
            return
        self._copy_to_clipboard(text)
        # Show a tiny toast near the mouse cursor
        try:
            x = self.winfo_pointerx()
            y = self.winfo_pointery()
            tw = tk.Toplevel(self)
            tw.wm_overrideredirect(True)
            tw.wm_geometry(f"+{x+10}+{y+10}")
            lbl = tk.Label(tw, text='Copied', bg='#333333', fg='#ffffff', bd=0, padx=6, pady=3)
            lbl.pack()
            tw.after(700, tw.destroy)
        except Exception:
            pass

    def _format_recent_text(self, sku: str, max_len: int = 28) -> str:
        s = str(sku)
        if len(s) <= max_len:
            return s
        return s[: max_len - 1] + '…'

    def _clear_console(self) -> None:
        """Remove all text from the console widget."""
        try:
            self.console_text.configure(state='normal')
            self.console_text.delete('1.0', 'end')
            self.console_text.configure(state='disabled')
        except Exception:
            pass

    def _open_console_log(self) -> None:
        try:
            open_console_log_file(CONSOLE_FILE_LOGGER.path)
        except Exception:
            pass

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

    # =================== UI UTILITIES ===================
    def _install_global_deselect_handlers(self) -> None:
        """Bind a global click to clear selection in console and suffix entry when clicking elsewhere."""
        top = self.winfo_toplevel()

        def is_descendant(child: tk.Widget | None, parent: tk.Widget | None) -> bool:
            try:
                w = child
                while w is not None:
                    if w is parent:
                        return True
                    w = w.master  # type: ignore[attr-defined]
            except Exception:
                return False
            return False

        def on_click(event):  # noqa: ANN001
            target = getattr(event, 'widget', None)
            # Clear console selection if click is outside console (focus will naturally move to clicked widget)
            try:
                if not is_descendant(target, self.console_text):
                    try:
                        # Attempt to remove selection without changing state
                        self.console_text.tag_remove('sel', '1.0', 'end')
                    except Exception:
                        # Fallback: toggle state temporarily
                        try:
                            prev = str(self.console_text.cget('state'))
                            self.console_text.configure(state='normal')
                            self.console_text.tag_remove('sel', '1.0', 'end')
                            self.console_text.configure(state=prev)
                        except Exception:
                            pass
                    # Ensure focus leaves the console: prefer clicked widget, else fallback to this frame
                    try:
                        if target is not None:
                            target.focus_set()
                        else:
                            self.focus_set()
                    except Exception:
                        try:
                            self.focus_set()
                        except Exception:
                            pass
            except Exception:
                pass
            # Clear suffix entry selection if click is outside suffix field
            try:
                if not is_descendant(target, getattr(self, '_suffix_entry', None)):
                    try:
                        self._suffix_entry.selection_clear()
                    except Exception:
                        pass
                    # Persist suffix on click-away
                    try:
                        self._persist_suffix()
                    except Exception:
                        pass
                    # Ensure focus leaves the suffix field similarly
                    try:
                        if target is not None:
                            target.focus_set()
                        else:
                            self.focus_set()
                    except Exception:
                        try:
                            self.focus_set()
                        except Exception:
                            pass
            except Exception:
                pass

        try:
            top.bind_all('<Button-1>', on_click, add=True)
        except Exception:
            pass

    def _on_click_create_sku_folder(self) -> None:
        suffix = ''
        try:
            suffix = (self._suffix_var.get() or '').strip()
        except Exception:
            pass
        # Delegate to app if available
        try:
            if callable(self._on_create_sku_folder):
                self._on_create_sku_folder(suffix)  # type: ignore[misc]
                return
        except Exception:
            pass
        # Fallback: notify in console
        self.console_neutral('Create SKU folder invoked (no handler wired).')

    # Hotkeys intentionally not bound; recents are mouse/touch only
    def _bind_recent_hotkeys(self) -> None:
        """Bind number keys 1–7 to copy the corresponding recent SKU."""
        top = self.winfo_toplevel()

        def handler_for_index(i: int):
            def _h(event=None):  # noqa: ANN001
                try:
                    self._on_recent_click(i)
                except Exception:
                    pass
            return _h

        for i in range(7):
            # Support both top-row digits and numpad digits
            sequences = (f"<Key-{i+1}>", f"<KP_{i+1}>")
            h = handler_for_index(i)
            for key in sequences:
                try:
                    top.bind_all(key, h, add=True)
                except Exception:
                    pass

    # =================== STATUS HELPERS ===================
    def set_status(self, *, online: bool, account: str | None, token_expiry_iso: str | None = None) -> None:
        label = 'Online' if online else 'Offline'
        if account:
            label += f' · {account}'
        self._status_var.set(label)
        # Apply color via widget style map
        try:
            color = '#22c55e' if online else '#6c757d'  # brighter green / gray
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
        """Bind function keys F1–F8 to launch favorites 1..8."""
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

        # Map F1..F8 to indices 0..7
        for i in range(8):
            key = f'<F{i+1}>'
            h = handler_for_index(i)
            try:
                top.bind_all(key, h, add=True)
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
