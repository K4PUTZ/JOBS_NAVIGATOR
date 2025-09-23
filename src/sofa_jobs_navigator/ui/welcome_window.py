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
        ttk.Label(root, text='\n\nWelcome to Sofa Jobs Navigator', font=('TkDefaultFont', 12, 'bold')).pack(pady=(0, 8))

        # Body text
        body = (
            '\n\nCopy once, detect many. Copy text from anywhere — file names, folder names, emails, web pages, chats—and press F12. The app instantly detects one or more SKUs in your clipboard and sets your Current SKU, so you’re ready to act without pasting or retyping.\n\n'
            'Open the right remote folder with one click or key. With the Current SKU set, a single click (or an F-key) jumps straight to the correct Google Drive folder or subfolder. It’s the fastest way to get from “I have a Vendor-ID” to “I’m working in the right place.”\n\n'
            'Save time with custom Favorites. Configure per-SKU favorites (F1–F8) that point to your most-used remote folders. These shortcuts standardize navigation across the team and cut repetitive browsing to nearly zero.\n\n'
            'Your recent SKUs, one-tap away. The app remembers the last SKUs you used and shows them as quick buttons. Copy any recent SKU in a click, with full values available in tooltips—perfect for fast reuse.\n\n'
            'Create a local folder named “SKU + suffix.” When you’re ready to stage local files, create a consistently named folder in your preferred location in one step. It complements the online workflow (the app is online-first) while ensuring clean, predictable naming on your machine.\n\n'
        )
        # Use a read-only text box with word wrapping so content wraps cleanly
        txt = tk.Text(root, wrap='word', height=16, width=80, takefocus=0)
        # Style it to look like part of the dialog (flat, no border) and match background (simulate transparency)
        try:
            bg = ''
            try:
                # Prefer ttk theme background if available
                style = ttk.Style(root)
                bg = style.lookup('TFrame', 'background') or ''
            except Exception:
                pass
            if not bg:
                try:
                    bg = root.cget('background')
                except Exception:
                    bg = ''
            if not bg:
                bg = self.cget('background') if hasattr(self, 'cget') else '#f0f0f0'
            # Match font with the rest of the program (use TLabel font or TkDefaultFont as fallback)
            try:
                default_font = style.lookup('TLabel', 'font') or 'TkDefaultFont'
            except Exception:
                default_font = 'TkDefaultFont'
            txt.configure(bg=bg, relief='flat', bd=0, highlightthickness=0, highlightbackground=bg, insertbackground='#000000', font=default_font)
        except Exception:
            try:
                txt.configure(relief='flat', bd=0, highlightthickness=0)
            except Exception:
                pass
        txt.insert('1.0', body)
        txt.configure(state='disabled')
        txt.pack(fill='x', expand=False, padx=8, pady=(0, 6))
        # Separator between text and buttons
        try:
            ttk.Separator(root, orient='horizontal').pack(fill='x', padx=8, pady=(0, 8))
        except Exception:
            pass
        # Auto-size height to fit all wrapped display lines so the window grows to accommodate text
        try:
            self.update_idletasks()
            display_lines = None
            try:
                # Count pixel-wrapped display lines if supported by Tk
                display_lines = int(txt.count('1.0', 'end', 'displaylines')[0])
            except Exception:
                pass
            if not display_lines or display_lines <= 0:
                try:
                    # Fallback to logical lines as a rough estimate
                    display_lines = int(txt.index('end-1c').split('.')[0])
                except Exception:
                    display_lines = 16
            # Apply height; add a small cushion
            txt.configure(height=max(1, display_lines))
        except Exception:
            pass

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
