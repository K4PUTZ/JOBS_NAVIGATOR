from __future__ import annotations

"""Welcome window — simplified and reliable centering."""

import tkinter as tk
from tkinter import ttk
from pathlib import Path

from ..utils.app_icons import set_app_icon


class WelcomeWindow(tk.Toplevel):
    """A minimal Welcome window that centers relative to the parent once."""

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

        self._build_ui()
        # Center once after the window is mapped; no withdraw/deiconify to avoid visibility issues
        try:
            self.after(0, self._center_once)
        except Exception:
            pass

    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=12)
        self._root = root
        root.pack(fill='both', expand=True)

        # Optional top image (Help1.png)
        self._image_ref = None  # keep reference alive
        self._try_load_top_image()

        # Heading
        ttk.Label(root, text='Welcome to Sofa Jobs Navigator', font=('TkDefaultFont', 12, 'bold')).pack(pady=(0, 8))

        # Body text
        body = (
            'Use Settings (F11) to choose your Working Folder.\n'
            'Connect to Google Drive (optional) to enable online lookups.\n'
            'Configure Favorites (F1–F8) for quick navigation under each SKU.\n'
            'Use Home to reopen this Help at any time.'
        )
        ttk.Label(root, text=body, justify='left', anchor='w').pack(anchor='w')

        # Buttons row
        btns = ttk.Frame(root)
        btns.pack(fill='x', pady=(12, 0))
        ttk.Frame(btns).pack(side='left', expand=True)
        ttk.Button(btns, text='Close', command=self.destroy).pack(side='right')

    def _try_load_top_image(self) -> None:
        """Attempt to load assets/help/Help1.png (or .webp) and place above content."""
        try:
            base = Path(__file__).resolve().parent
            candidates = [base / 'assets' / 'help' / 'Help1.png', base / 'assets' / 'help' / 'Help1.webp']
            img_path = next((p for p in candidates if p.exists()), None)
            if not img_path:
                return
            if img_path.suffix.lower() == '.png':
                self._image_ref = tk.PhotoImage(file=str(img_path))
            else:
                try:
                    from PIL import Image, ImageTk  # type: ignore
                    self._image_ref = ImageTk.PhotoImage(Image.open(str(img_path)))
                except Exception:
                    self._image_ref = None
            if self._image_ref is not None:
                lbl = tk.Label(self._root, image=self._image_ref, bd=0)
                lbl.pack(pady=(0, 8))
        except Exception:
            # Silent failure: image is optional
            self._image_ref = None

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
