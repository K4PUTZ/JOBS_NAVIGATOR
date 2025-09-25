from __future__ import annotations

"""Help/Welcome window — multipage with navigation and page indicators."""

import tkinter as tk
from tkinter import ttk
from pathlib import Path

from ..utils.app_icons import set_app_icon
from ..version import VERSION


class WelcomeWindow(tk.Toplevel):
    """Multipage Help / Welcome window (7 pages) with simple navigation.

    Layout per page:
      • Image (600x300) centered
      • A wrapped text paragraph
      • Navigation row: [Previous]  •••••••  [Next/Finish]

    This version hard‑codes the final desired page order (no runtime rotation).
    """

    def __init__(self, master: tk.Misc) -> None:
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

        # Pages state containers (populated in _load_pages)
        self._page_count: int = 0
        self._current_page: int = 0
        self._pages: list[dict[str, object]] = []   # {'image': PhotoImage|None, 'text': str}
        self._image_refs: list[object | None] = []  # keep images alive

        # Build UI and show first page
        self._build_ui()
        self._load_pages()
        self._update_page()
        # Center once after the window is mapped; no withdraw/deiconify to avoid visibility issues
        try:
            self.after(0, self._center_once)
        except Exception:
            pass
        # Keyboard navigation: Left/Right arrows
        try:
            self.bind('<Left>', lambda e: self._go_prev())
            self.bind('<Right>', lambda e: self._go_next())
        except Exception:
            pass

    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=12)
        self._root = root
        root.pack(fill='both', expand=True)

        # Content area (image + text)
        content = ttk.Frame(root)
        content.pack(fill='both', expand=True)
        # Two empty spacer lines above the image
        try:
            ttk.Frame(content, height=8).pack(fill='x')
            ttk.Frame(content, height=8).pack(fill='x')
        except Exception:
            pass
        # Image holder (centered)
        self._img_label = tk.Label(content, bd=0)
        self._img_label.pack(pady=(0, 8), anchor='center')
        # Small text under image (reduced width to ~75% for better readability)
        self._text_label = ttk.Label(content, text='', wraplength=420, justify='center')
        self._text_label.pack(pady=(0, 8), anchor='center')

        # Separator above navigation
        try:
            ttk.Separator(root, orient='horizontal').pack(fill='x', padx=8, pady=(8, 8))
        except Exception:
            pass

        # Navigation row: [Prev] [dots] [Next/Finish]
        nav = ttk.Frame(root)
        nav.pack(fill='x')
        # Previous button (left)
        self._btn_prev = ttk.Button(nav, text='Previous', command=self._go_prev)
        self._btn_prev.pack(side='left')
        # Dots panel (center)
        dots_holder = ttk.Frame(nav)
        dots_holder.pack(side='left', expand=True)
        self._dots_frame = ttk.Frame(dots_holder)
        self._dots_frame.pack()
        # Next/Finish button (right)
        self._btn_next = ttk.Button(nav, text='Next', command=self._go_next)
        self._btn_next.pack(side='right')

    # --------- Pages: loading, navigation, rendering ---------
    def _load_pages(self) -> None:
        """Load pages (images + text) in their final intended order.

        Order is now permanent (no runtime rotation):
          1. Welcome / high‑level rationale
          2. Clipboard SKU detection
          3. One‑click navigation
          4. Favorites
          5. Recent SKUs
          6. Local folder creation
          7. Finish
        """
        base = Path(__file__).resolve().parent / 'assets' / 'help'
        self._pages.clear()
        self._image_refs.clear()

        texts: list[str] = [
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

        self._page_count = len(texts)
        for idx, text in enumerate(texts, start=1):
            img = self._load_image_variant(base, f'Help{idx}')
            self._pages.append({'image': img, 'text': text})
            self._image_refs.append(img)

    def _load_image_variant(self, base: Path, stem: str):
        """Load and resize image 'stem.(png|webp)' to 600x300; return PhotoImage or None."""
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
            try:
                resample = getattr(Image, 'LANCZOS', getattr(Image, 'ANTIALIAS', 1))
            except Exception:
                resample = 1
            im = im.resize(target_size, resample)
            return ImageTk.PhotoImage(im)
        except Exception:
            # Fallback: only PNG via Tk
            try:
                if img_path.suffix.lower() == '.png':
                    return tk.PhotoImage(file=str(img_path))
            except Exception:
                return None
        return None

    def _go_prev(self) -> None:
        if self._current_page <= 0:
            return
        self._current_page -= 1
        self._update_page()

    def _go_next(self) -> None:
        if self._current_page < self._page_count - 1:
            self._current_page += 1
            self._update_page()
            return
        # Finish on last page
        try:
            self.destroy()
        except Exception:
            pass

    def _update_page(self) -> None:
        if not (0 <= self._current_page < self._page_count):
            return
        page = self._pages[self._current_page]
        img = page.get('image')  # type: ignore[assignment]
        txt = page.get('text')   # type: ignore[assignment]
        # Update widgets
        self._img_label.configure(image=img if img else '')
        self._img_label.image = img  # keep ref
        self._text_label.configure(text=str(txt or ''))
        # Buttons
        if self._current_page == 0:
            self._btn_prev.state(['disabled'])
        else:
            self._btn_prev.state(['!disabled'])
        self._btn_next.configure(text='Finish' if self._current_page == self._page_count - 1 else 'Next')
        # Indicators & centering
        self._render_indicators()
        self.after(0, self._center_once)

    def _render_indicators(self) -> None:
        # Clear existing dots
        for child in self._dots_frame.winfo_children():
            child.destroy()
        pad = 6
        for i in range(self._page_count):
            active = (i == self._current_page)
            size = 12 if active else 8
            c = tk.Canvas(self._dots_frame, width=size + pad, height=size + pad, highlightthickness=0, bd=0)
            c.pack(side='left')
            x0 = pad // 2
            y0 = pad // 2
            x1 = x0 + size
            y1 = y0 + size
            if active:
                glow_pad = 3
                c.create_oval(x0 - glow_pad, y0 - glow_pad, x1 + glow_pad, y1 + glow_pad, fill='#eaeaea', outline='')
                c.create_oval(x0, y0, x1, y1, fill='#ffffff', outline='#d0d0d0')
            else:
                c.create_oval(x0, y0, x1, y1, fill='#cfcfcf', outline='#d9d9d9')

    def _center_once(self) -> None:
        if getattr(self, '_centered', False):
            return
        self._centered = True
        self.update_idletasks()
        w = self.winfo_reqwidth() or self.winfo_width()
        h = self.winfo_reqheight() or self.winfo_height()
        parent = self.master if isinstance(self.master, tk.Misc) else None
        if parent is not None:
            parent.update_idletasks()
            mx, my = parent.winfo_rootx(), parent.winfo_rooty()
            mw = parent.winfo_width() or parent.winfo_reqwidth()
            mh = parent.winfo_height() or parent.winfo_reqheight()
            x = mx + max((mw - w) // 2, 0)
            y = my + max((mh - h) // 2, 0)
        else:
            sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
            x = max((sw - w) // 2, 0)
            y = max((sh - h) // 2, 0)
        self.geometry(f"{w}x{h}+{x}+{y}")
        try:
            self.lift()
            self.focus_set()
        except Exception:
            pass
