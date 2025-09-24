from __future__ import annotations

"""Help/Welcome window — multipage with navigation and page indicators."""

import tkinter as tk
from tkinter import ttk
from pathlib import Path

from ..utils.app_icons import set_app_icon


class WelcomeWindow(tk.Toplevel):
    """A multipage Help window with 6 pages and navigation controls.

    Layout per page:
    - Top: transparent 600x300 image centered
    - Middle: small text paragraph
    - Bottom: navigation row with [Previous] [dots] [Next/Finish]
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

        # Pages state
        self._page_count = 6
        self._current_page = 0
        self._pages: list[dict[str, object]] = []  # {'image': PhotoImage|None, 'text': str}
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
        # Small text under image
        self._text_label = ttk.Label(content, text='', wraplength=560, justify='center')
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
        """Load up to 6 pages: images (png/webp) and small texts."""
        base = Path(__file__).resolve().parent / 'assets' / 'help'
        self._pages.clear()
        self._image_refs.clear()
        texts = [
            'Copy once, detect many.\n\nCopy text from anywhere—file names, folder names, emails, web pages, chats—and press F12. The app instantly search the text and detects one or more SKUs in your clipboard. The first detected SKU will become your Current SKU, so you’re ready to act without pasting or retyping.',
            'With the Current SKU set, a single click (or key press) jumps straight to the correct Google Drive folder or subfolder. It’s the fastest way to get from “I have a Vendor-ID” to “I’m working in the right place.”',
            'Save time with custom Favorites. Configure per-SKU favorites (F1–F8) that point to your most-used remote folders. These shortcuts standardize navigation and cut repetitive browsing to nearly zero.',
            'Your recent SKUs, one-tap away. The app remembers the last SKUs you used and shows them as quick buttons. Copy any recent SKU in a click, with full values available in tooltips—perfect for fast reuse.',
            'Create a local folder named “SKU + suffix.” Create a consistently named folder in your preferred location in one step, while ensuring clean, predictable naming on your machine.',
            'All set—enjoy faster, safer navigation. Press Finish to begin working.',
        ]
        for i in range(self._page_count):
            idx = i + 1
            img = self._load_image_variant(base, f'Help{idx}')
            self._pages.append({'image': img, 'text': texts[i] if i < len(texts) else ''})
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
        if self._current_page > 0:
            self._current_page -= 1
            self._update_page()

    def _go_next(self) -> None:
        if self._current_page < self._page_count - 1:
            self._current_page += 1
            self._update_page()
        else:
            # Finish
            try:
                self.destroy()
            except Exception:
                pass

    def _update_page(self) -> None:
        # Update image
        page = self._pages[self._current_page] if 0 <= self._current_page < len(self._pages) else None
        img = page.get('image') if isinstance(page, dict) else None
        txt = page.get('text') if isinstance(page, dict) else ''
        try:
            self._img_label.configure(image=img if img is not None else '')
            self._img_label.image = img  # keep ref on label too
        except Exception:
            pass
        try:
            self._text_label.configure(text=str(txt or ''))
        except Exception:
            pass
        # Update buttons
        try:
            if self._current_page == 0:
                self._btn_prev.state(['disabled'])
            else:
                self._btn_prev.state(['!disabled'])
            if self._current_page == self._page_count - 1:
                self._btn_next.configure(text='Finish')
            else:
                self._btn_next.configure(text='Next')
        except Exception:
            pass
        # Re-render indicators
        self._render_indicators()
        # Recenter once content settles
        try:
            self.after(0, self._center_once)
        except Exception:
            pass

    def _render_indicators(self) -> None:
        # Clear previous
        for child in list(self._dots_frame.winfo_children()):
            try:
                child.destroy()
            except Exception:
                pass
        # Draw dots as small canvases
        for i in range(self._page_count):
            is_active = (i == self._current_page)
            size = 12 if is_active else 8
            pad = 6
            c = tk.Canvas(self._dots_frame, width=size + pad, height=size + pad, highlightthickness=0, bd=0)
            c.pack(side='left')
            x0 = pad // 2
            y0 = pad // 2
            x1 = x0 + size
            y1 = y0 + size
            if is_active:
                # Outer glow (subtle)
                try:
                    glow_pad = 3
                    c.create_oval(x0 - glow_pad, y0 - glow_pad, x1 + glow_pad, y1 + glow_pad, fill='#eaeaea', outline='')
                except Exception:
                    pass
                # Main white circle with light outline
                c.create_oval(x0, y0, x1, y1, fill='#ffffff', outline='#d0d0d0')
            else:
                # Light gray small circle
                c.create_oval(x0, y0, x1, y1, fill='#cfcfcf', outline='#d9d9d9')

    def _center_once(self) -> None:
        # Guard against repeated centering
        if getattr(self, '_centered', False):
            return
        setattr(self, '_centered', True)
        try:
            # Ensure widgets have computed requested size
            self.update_idletasks()
            w = self.winfo_reqwidth() or self.winfo_width()
            h = self.winfo_reqheight() or self.winfo_height()
            # Prefer centering relative to parent window coordinates
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
            try:
                self.lift()
            except Exception:
                pass
            try:
                self.focus_set()
            except Exception:
                pass
        except Exception:
            pass
