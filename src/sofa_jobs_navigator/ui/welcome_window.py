"""Welcome/Help wizard for Sofa Jobs Navigator."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from pathlib import Path
from typing import Callable, Sequence

from ..utils.app_icons import set_app_icon


class WelcomeWindow(tk.Toplevel):
    """A simple wizard-like window with images and text pages.

    Pages (index):
      0: Quick README / intro
      1: Set Working Folder
      2: Authentication
      3: Favorites shortcuts (dynamic)
      4: Recent SKUs usage
    """

    def __init__(
        self,
        master: tk.Misc,
        *,
        on_set_show_at_startup: Callable[[bool], None] | None = None,
        initial_show_at_startup: bool = True,
        image_dir: str | Path | None = None,
    ) -> None:
        super().__init__(master)
        self.title('Welcome · Sofa Jobs Navigator')
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()
        try:
            set_app_icon(self)
        except Exception:
            pass

        self._on_set_show = on_set_show_at_startup
        self._show_var = tk.BooleanVar(value=bool(initial_show_at_startup))
        self._page = 0
        self._page_count = 5
        self._image_dir = Path(image_dir) if image_dir else None

        self._build_ui()
        self._render_page()
        self._ensure_front_and_center()
        try:
            # Re-center when the window is shown/mapped
            self.bind('<Map>', lambda e: self._ensure_front_and_center())
            # Also re-center and bring to front right after creation and on visibility/focus changes
            self.after(0, self._ensure_front_and_center)
            self.bind('<Visibility>', lambda e: self._ensure_front_and_center())
            self.bind('<FocusIn>', lambda e: self._ensure_front_and_center())
        except Exception:
            pass

    # -------------------- UI --------------------
    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=12)
        root.pack(fill='both', expand=True)

        # Image placeholder frame (fixed size ~400x280)
        self._image_holder = tk.Canvas(root, width=400, height=280, bg='#f0f0f0', highlightthickness=0)
        self._image_holder.pack()

        # Text area (centered)
        self._text = ttk.Label(root, text='', justify='center', anchor='center', wraplength=520)
        self._text.pack(pady=(8, 12))

        # Page indicators (dots)
        self._dots = ttk.Frame(root)
        self._dots.pack(pady=(0, 8))

        # Bottom row: left Prev, center checkbox + tip, right Next
        bottom = ttk.Frame(root)
        bottom.pack(fill='x')
        bottom.columnconfigure(0, weight=1)
        bottom.columnconfigure(1, weight=1)
        bottom.columnconfigure(2, weight=1)

        self._prev_btn = ttk.Button(bottom, text='← Previous', command=self._go_prev)
        self._prev_btn.grid(row=0, column=0, sticky='w')

        center = ttk.Frame(bottom)
        center.grid(row=0, column=1)
        ttk.Checkbutton(center, text='Show at startup', variable=self._show_var, command=self._apply_show_pref).pack()
        ttk.Label(center, text='Tip: You can reset these messages in Settings.', foreground='#6c757d').pack(pady=(4, 0))

        self._next_btn = ttk.Button(bottom, text='Next →', command=self._go_next)
        self._next_btn.grid(row=0, column=2, sticky='e')

    # -------------------- Rendering --------------------
    def _render_page(self) -> None:
        # Update image area (load WebP/PNG if provided)
        self._load_image_for_page(self._page)
        # Text content for each page
        texts = [
            (
                'Welcome to Sofa Jobs Navigator\n\n'
                'A quick utility to navigate project folders by SKU, manage shortcuts, and speed up your workflow.'
            ),
            (
                'Set your Working Folder\n\n'
                'Open Settings and choose a local folder where your SKU folders will be created and organized.'
            ),
            (
                'Sign in to Google Drive (optional)\n\n'
                'Use Connect/Refresh to authenticate for online lookups. You can run offline to just manage local folders.'
            ),
            (
                'Favorites (F1–F8)\n\n'
                'Configure relative paths under SKU root (e.g., "Design/Final"). Press F1–F8 to open them quickly.'
            ),
            (
                'Recent SKUs\n\n'
                'Detected SKUs appear here for quick copy. Click to copy or press 1–7/NumPad 1–7 to copy the matching SKU.'
            ),
        ]
        try:
            self._text.configure(text=texts[self._page])
        except Exception:
            pass
        self._render_dots()
        # Update buttons enabled/disabled
        self._prev_btn.configure(state=(tk.NORMAL if self._page > 0 else tk.DISABLED))
        self._next_btn.configure(text=('Finish' if self._page >= self._page_count - 1 else 'Next →'))
        # Re-center after content changes (height may vary by page)
        self._center_on_screen()

    def _render_dots(self) -> None:
        # Clear and rebuild dots
        for child in list(self._dots.children.values()):
            try:
                child.destroy()
            except Exception:
                pass
        for i in range(self._page_count):
            size = 10
            c = tk.Canvas(self._dots, width=size, height=size, highlightthickness=0, bg=self._dots.cget('background'))
            fill = '#0078d4' if i == self._page else '#c0c0c0'
            c.create_oval(1, 1, size-1, size-1, fill=fill, outline=fill)
            c.pack(side='left', padx=4)

    def _go_prev(self) -> None:
        if self._page > 0:
            self._page -= 1
            self._render_page()

    def _go_next(self) -> None:
        if self._page < self._page_count - 1:
            self._page += 1
            self._render_page()
        else:
            # Finish closes the window
            self.destroy()

    # -------------------- Preferences --------------------
    def _apply_show_pref(self) -> None:
        try:
            if self._on_set_show:
                self._on_set_show(bool(self._show_var.get()))
        except Exception:
            pass

    # -------------------- Image loading --------------------
    def _load_image_for_page(self, page: int) -> None:
        # Clear previous image content
        try:
            self._image_holder.delete('all')
        except Exception:
            pass
        # Try to load from provided image dir
        img_path: Path | None = None
        if self._image_dir is not None:
            # Look for Help{n}.webp or Help{n}.png (1-based numbering)
            idx = page + 1
            for ext in ('.webp', '.png'):
                cand = self._image_dir / f'Help{idx}{ext}'
                if cand.exists():
                    img_path = cand
                    break
        if img_path is None:
            # Draw placeholder frame
            w, h = 400, 280
            self._image_holder.create_rectangle(2, 2, w-2, h-2, outline='#aaaaaa', width=2)
            self._image_holder.create_text(w//2, h//2, text='Image Placeholder', fill='#666666')
            return
        # Load image best-effort (PNG is native; WebP needs Pillow)
        try:
            if str(img_path).lower().endswith('.png'):
                self._img = tk.PhotoImage(file=str(img_path))  # keep reference on instance
            else:
                # Try Pillow for WebP
                from PIL import Image, ImageTk  # type: ignore
                im = Image.open(str(img_path))
                self._img = ImageTk.PhotoImage(im)
            # Center it
            w, h = 400, 280
            x = (w - self._img.width()) // 2
            y = (h - self._img.height()) // 2
            self._image_holder.create_image(x, y, anchor='nw', image=self._img)
        except Exception:
            # Fallback to placeholder if load fails
            w, h = 400, 280
            self._image_holder.create_rectangle(2, 2, w-2, h-2, outline='#aaaaaa', width=2)
            self._image_holder.create_text(w//2, h//2, text='Image load failed', fill='#666666')

    # -------------------- Helpers --------------------
    def _ensure_front_and_center(self) -> None:
        try:
            self._center_on_screen()
            try:
                self.lift()
            except Exception:
                pass
            try:
                self.focus_force()
            except Exception:
                pass
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
