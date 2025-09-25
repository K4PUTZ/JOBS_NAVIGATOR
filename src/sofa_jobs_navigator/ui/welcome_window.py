from __future__ import annotations

"""Welcome / Help window with interactive onboarding controls on select pages."""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

from ..utils.app_icons import set_app_icon
from ..version import VERSION


class WelcomeWindow(tk.Toplevel):
    """Onboarding / Help window.

    Pages (0-based):
      0) Overview + Connect button
      1) Clipboard detection explanation
      2) Navigation explanation
      3) Favorites (Set Favorites button)
      4) Recents explanation
      5) Working Folder picker
      6) Final toggles (sounds / connect on startup / open root)
    """

    def __init__(
        self,
        master: tk.Misc,
        *,
        settings=None,
        on_auth_connect=None,
        on_open_settings=None,
        is_connected=None,
        save_settings=None,
    ) -> None:
        super().__init__(master)
        self.title('Welcome · Sofa Jobs Navigator')
        self.resizable(False, False)
        try:
            self.transient(master)
        except Exception:
            pass
        try:
            set_app_icon(self)
        except Exception:
            pass

        # External references / callbacks
        self._settings = settings
        self._cb_auth_connect = on_auth_connect
        self._cb_open_settings = on_open_settings
        self._cb_is_connected = is_connected
        self._cb_save_settings = save_settings

        # Page state
        self._page_count = 0
        self._current_page = 0
        self._pages: list[dict[str, object]] = []
        self._image_refs: list[object | None] = []

        self._build_ui()
        self._load_pages()
        self._update_page()
        # Content-based sizing (remove large fixed 720px min height)
        try:
            self.update_idletasks()
            w = max(self.winfo_width(), 640)
            h = self.winfo_height()  # just enough for current content
            self.minsize(w, h)
        except Exception:
            pass
        try:
            self.after(0, self._center_once)
        except Exception:
            pass
        try:
            self.bind('<Left>', lambda e: self._go_prev())
            self.bind('<Right>', lambda e: self._go_next())
            self.bind('<Escape>', lambda e: self.destroy())
        except Exception:
            pass

    # ---------- UI Construction ----------
    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=14)
        root.pack(fill='both', expand=True)
        self._root = root

        content = ttk.Frame(root)
        content.pack(fill='both', expand=True)
        for _ in range(2):
            ttk.Frame(content, height=8).pack(fill='x')
        self._img_label = tk.Label(content, bd=0)
        self._img_label.pack(pady=(0, 8))
        self._text_label = ttk.Label(content, text='', wraplength=420, justify='center')
        self._text_label.pack(pady=(0, 8))
        ttk.Separator(root, orient='horizontal').pack(fill='x', padx=8, pady=(4, 4))
        self._extra_frame = ttk.Frame(root)
        self._extra_frame.pack(fill='x')

        nav = ttk.Frame(root)
        nav.pack(fill='x', pady=(4, 0))
        self._btn_prev = ttk.Button(nav, text='Previous', command=self._go_prev)
        self._btn_prev.pack(side='left')
        dots_holder = ttk.Frame(nav)
        dots_holder.pack(side='left', expand=True)
        self._dots_frame = ttk.Frame(dots_holder)
        self._dots_frame.pack()
        self._btn_next = ttk.Button(nav, text='Next', command=self._go_next)
        self._btn_next.pack(side='right')

    # ---------- Pages Data ----------
    def _load_pages(self) -> None:
        base = Path(__file__).resolve().parent / 'assets' / 'help'
        self._pages.clear(); self._image_refs.clear()
        texts = [
            (
                f"Welcome to Sofa Jobs Navigator® – {VERSION}.\n\n"
                "Copy any Vendor-ID or SKU, press F12, and jump straight to the correct Google Drive folder. "
                "Work directly in your browser to avoid sync conflicts, forced app updates, cache corruption, "
                "disk space issues, and crashes. The browser is reliable, consistent, and instant."
            ),
            (
                "Copy once, detect many.\n\n"
                "Copy large texts from anywhere — file names, folder names, emails, web pages, chats — and press F12. "
                "The app scans your clipboard and detects all SKUs. The first valid one becomes your 'CURRENT SKU' so "
                "you can act immediately, without pasting or retyping."
            ),
            (
                "Open the right remote folder instantly.\n\n"
                "With a 'CURRENT SKU' set, a click (or hotkey) jumps straight to its Google Drive folder or a mapped subfolder. "
                "Use F1–F8 or sidebar buttons for fast, repeatable navigation—going from Vendor-ID to working context in seconds."
            ),
            (
                "Save time with Favorites.\n\n"
                "Configure per-SKU favorites (F1–F8) pointing at your most-used remote folders. "
                "Standardize structure and eliminate repetitive wandering through deep paths."
            ),
            (
                "Recent SKUs one tap away.\n\n"
                "The side panel keeps the last SKUs you touched. Click to copy or reuse them—tooltips show full values. "
                "You can detect and load up to 7 SKUs at once to the recents panel, and cycle through multiple SKUs quickly while tracking parallel work."
            ),
            (
                "Create a local folder named “SKU + suffix.”\n\n"
                "Generate a consistently named local folder in one step. Clean, predictable naming helps keep local workspaces tidy."
            ),
            (
                "All set!\n\n"
                "Enjoy faster, safer navigation and a reduced cognitive load. Press Finish to begin working."
            ),
        ]
        for idx, text in enumerate(texts, start=1):
            img = self._load_image_variant(base, f'Help{idx}')
            self._pages.append({'image': img, 'text': text})
            self._image_refs.append(img)
        self._page_count = len(texts)

    @staticmethod
    def _load_image_variant(base: Path, stem: str):
        target_size = (600, 300)
        candidates = [base / f'{stem}.png', base / f'{stem}.webp']
        img_path = next((p for p in candidates if p.exists()), None)
        if not img_path:
            return None
        try:
            from PIL import Image, ImageTk  # type: ignore
            im = Image.open(str(img_path))
            try:
                im = im.convert('RGBA')
            except Exception:
                pass
            resample = getattr(__import__('PIL').Image, 'LANCZOS', 1)
            im = im.resize(target_size, resample)
            return ImageTk.PhotoImage(im)
        except Exception:
            try:
                if img_path.suffix.lower() == '.png':
                    return tk.PhotoImage(file=str(img_path))
            except Exception:
                return None
        return None

    # ---------- Navigation ----------
    def _go_prev(self) -> None:
        if self._current_page <= 0:
            return
        self._current_page -= 1
        self._update_page()

    def _go_next(self) -> None:
        # Soft warnings
        try:
            if self._current_page == 0 and callable(self._cb_is_connected):
                if not bool(self._cb_is_connected()):
                    messagebox.showwarning(
                        title='Not connected',
                        message='You are not connected; remote folder search will be limited until you connect.\nPress F11 later to open Settings.',
                        parent=self,
                    )
            if self._current_page == 5 and self._settings is not None:
                wf = (self._settings.working_folder or '').strip()
                if not wf:
                    messagebox.showwarning(
                        title='Working Folder not set',
                        message='Without a Working Folder you cannot create local SKU folders in one click.\nPress F11 later to open Settings.',
                        parent=self,
                    )
        except Exception:
            pass
        # Persist toggles on final page
        if self._current_page == self._page_count - 1 and self._settings is not None:
            try:
                if hasattr(self, '_sounds_var'):
                    self._settings.sounds_enabled = bool(self._sounds_var.get())
                if hasattr(self, '_connect_var'):
                    self._settings.connect_on_startup = bool(self._connect_var.get())
                if hasattr(self, '_open_root_var'):
                    self._settings.open_root_on_sku_found = bool(self._open_root_var.get())
                if callable(self._cb_save_settings):
                    self._cb_save_settings()
            except Exception:
                pass
        if self._current_page < self._page_count - 1:
            self._current_page += 1
            self._update_page()
        else:
            try:
                self.destroy()
            except Exception:
                pass

    # ---------- Rendering ----------
    def _update_page(self) -> None:
        if not (0 <= self._current_page < self._page_count):
            return
        page = self._pages[self._current_page]
        img = page.get('image'); txt = page.get('text')
        self._img_label.configure(image=img if img else '')
        self._img_label.image = img
        self._text_label.configure(text=str(txt or ''))
        self._btn_prev.state(['disabled'] if self._current_page == 0 else ['!disabled'])
        self._btn_next.configure(text='Finish' if self._current_page == self._page_count - 1 else 'Next')
        self._render_indicators()
        self._render_extra_controls()
        self.after(0, self._center_once)

    def _render_indicators(self) -> None:
        for child in list(self._dots_frame.winfo_children()):
            child.destroy()
        pad = 6
        for i in range(self._page_count):
            active = (i == self._current_page)
            size = 12 if active else 8
            c = tk.Canvas(self._dots_frame, width=size + pad, height=size + pad, highlightthickness=0, bd=0)
            c.pack(side='left')
            x0 = pad // 2; y0 = pad // 2; x1 = x0 + size; y1 = y0 + size
            if active:
                glow_pad = 3
                c.create_oval(x0 - glow_pad, y0 - glow_pad, x1 + glow_pad, y1 + glow_pad, fill='#eaeaea', outline='')
                c.create_oval(x0, y0, x1, y1, fill='#ffffff', outline='#d0d0d0')
            else:
                c.create_oval(x0, y0, x1, y1, fill='#cfcfcf', outline='#d9d9d9')

    def _render_extra_controls(self) -> None:
        for child in list(self._extra_frame.winfo_children()):
            child.destroy()
        p = self._current_page
        if p not in (0, 3, 5, 6):
            return
        for _ in range(2):
            ttk.Frame(self._extra_frame, height=8).pack(fill='x')
        try:
            if p == 0:
                row = ttk.Frame(self._extra_frame); row.pack(fill='x')
                ttk.Label(row, text='To begin, we must connect to Google Drive.').pack(side='left')
                ttk.Button(row, text='Connect', command=self._on_press_auth).pack(side='left', padx=(12, 0))
            elif p == 3:
                row = ttk.Frame(self._extra_frame); row.pack(fill='x')
                ttk.Label(row, text='You can set your favorite shortcuts in the settings now, or press F11 later.').pack(side='left')
                ttk.Button(row, text='Set Favorites', command=self._on_press_open_settings).pack(side='left', padx=(12, 0))
            elif p == 5:
                ttk.Label(self._extra_frame, text='Choose your Working Folder, where you keep your projects:').pack(anchor='w')
                browse = ttk.Frame(self._extra_frame); browse.pack(fill='x', pady=(4, 0))
                current = '' if not self._settings else (self._settings.working_folder or '')
                self._wf_var = tk.StringVar(value=current)
                self._wf_entry = ttk.Entry(browse, textvariable=self._wf_var, width=54, state='readonly')
                self._wf_entry.pack(side='left', padx=(0, 6))
                ttk.Button(browse, text='Browse…', command=self._pick_working_folder).pack(side='left')
            elif p == 6:
                sounds = bool(getattr(self._settings, 'sounds_enabled', True)) if self._settings else True
                connect = bool(getattr(self._settings, 'connect_on_startup', False)) if self._settings else False
                open_root = bool(getattr(self._settings, 'open_root_on_sku_found', False)) if self._settings else False
                self._sounds_var = tk.BooleanVar(value=sounds)
                self._connect_var = tk.BooleanVar(value=connect)
                self._open_root_var = tk.BooleanVar(value=open_root)
                for text, var in [
                    ('Sounds on', self._sounds_var),
                    ('Connect on startup', self._connect_var),
                    ('Open root folder on SKU found', self._open_root_var),
                ]:
                    ttk.Checkbutton(self._extra_frame, variable=var, text=text).pack(anchor='w')
        except Exception:
            pass
        for _ in range(2):
            ttk.Frame(self._extra_frame, height=8).pack(fill='x')

    # ---------- Actions ----------
    def _on_press_auth(self) -> None:
        if callable(self._cb_auth_connect):
            try:
                self._cb_auth_connect()
            except Exception as exc:
                try:
                    messagebox.showerror(title='Auth failed', message=str(exc), parent=self)
                except Exception:
                    pass

    def _on_press_open_settings(self) -> None:
        if callable(self._cb_open_settings):
            try:
                self._cb_open_settings()
            except Exception:
                pass

    def _pick_working_folder(self) -> None:
        current = getattr(self, '_wf_var', None).get() if hasattr(self, '_wf_var') else ''
        try:
            chosen = filedialog.askdirectory(parent=self, initialdir=current or None, title='Select working folder')
        except Exception:
            chosen = ''
        if chosen:
            try:
                self._wf_entry.configure(state='normal')
                self._wf_var.set(chosen)
                self._wf_entry.configure(state='readonly')
            except Exception:
                pass
            if self._settings is not None:
                try:
                    self._settings.working_folder = chosen
                    if callable(self._cb_save_settings):
                        self._cb_save_settings()
                except Exception:
                    pass

    # ---------- Utility ----------
    def _center_once(self) -> None:
        if getattr(self, '_centered', False):
            return
        self._centered = True
        self.update_idletasks()
        w = self.winfo_reqwidth() or self.winfo_width(); h = self.winfo_reqheight() or self.winfo_height()
        parent = self.master if isinstance(self.master, tk.Misc) else None
        if parent is not None:
            try:
                parent.update_idletasks()
            except Exception:
                pass
            mx, my = parent.winfo_rootx(), parent.winfo_rooty()
            mw = parent.winfo_width() or parent.winfo_reqwidth(); mh = parent.winfo_height() or parent.winfo_reqheight()
            x = mx + max((mw - w)//2, 0); y = my + max((mh - h)//2, 0)
        else:
            sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
            x = max((sw - w)//2, 0); y = max((sh - h)//2, 0)
        self.geometry(f"{w}x{h}+{x}+{y}")
        try:
            self.lift(); self.focus_set()
        except Exception:
            pass
