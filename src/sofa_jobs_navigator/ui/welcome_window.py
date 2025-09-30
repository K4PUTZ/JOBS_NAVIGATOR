from __future__ import annotations

"""Welcome / Help window with interactive onboarding controls on select pages."""

import sys
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
      6) Comprehensive Settings (all checkbox preferences)
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
        # Fixed sizing so every page fits consistently (no dynamic shrink/grow)
        try:
            self.update_idletasks()
            # Determine required space; enforce a stable baseline height for tallest page
            req_w = max(640, self._root_frame.winfo_reqwidth(), self.winfo_width())
            req_h = max(600, self._root_frame.winfo_reqheight(), self.winfo_height())
            self.minsize(req_w, req_h)
            self.geometry(f"{req_w}x{req_h}")
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
        root_frame = ttk.Frame(self, padding=14)
        root_frame.pack(fill='both', expand=True)
        self._root_frame = root_frame

        content = ttk.Frame(root_frame)
        content.pack(fill='both', expand=True)
        for _ in range(2):
            ttk.Frame(content, height=8).pack(fill='x')
        self._img_label = tk.Label(content, bd=0)
        self._img_label.pack(pady=(0, 8))
        self._text_label = ttk.Label(content, text='', wraplength=420, justify='center')
        self._text_label.pack(pady=(0, 8))
        ttk.Separator(root_frame, orient='horizontal').pack(fill='x', padx=8, pady=(4, 4))
        self._extra_frame = ttk.Frame(root_frame)
        self._extra_frame.pack(fill='x')

        nav = ttk.Frame(root_frame)
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
                "Good to go!\n\n"
                "If you wish to change your preferences later, just press F11.\n"
                "Click Finish to save your choices and begin working."
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
        # Validation and warnings for specific pages
        try:
            # Page 1 (index 0): Check connection status
            if self._current_page == 0 and callable(self._cb_is_connected):
                if not bool(self._cb_is_connected()):
                    proceed = messagebox.askyesno(
                        title='Not Connected',
                        message=(
                            "You are not connected to Google Drive. You won't be able to search remote folders until you connect.\n\n"
                            "Proceed without connecting now? You can press F11 later to open Settings and connect."
                        ),
                        parent=self,
                    )
                    if not proceed:
                        return
            
            # Page 6 (index 5): Validate working folder
            if self._current_page == 5 and self._settings is not None:
                wf = (self._settings.working_folder or '').strip()
                # Check if working folder is empty or invalid
                if not wf:
                    messagebox.showwarning(
                        title='Working Folder Not Set',
                        message='Without a Working Folder you won\'t be able to create SKU folders in one click.\n\nYou can press F11 later to open Settings and configure it.',
                        parent=self,
                    )
                else:
                    # Check if the folder actually exists
                    try:
                        folder_path = Path(wf)
                        if not folder_path.exists() or not folder_path.is_dir():
                            messagebox.showwarning(
                                title='Working Folder Invalid',
                                message=f'The Working Folder path is not valid or does not exist:\n{wf}\n\nYou won\'t be able to create SKU folders in one click. You can press F11 later to open Settings and configure it.',
                                parent=self,
                            )
                    except Exception:
                        messagebox.showwarning(
                            title='Working Folder Invalid',
                            message=f'The Working Folder path is not valid:\n{wf}\n\nYou won\'t be able to create SKU folders in one click. You can press F11 later to open Settings and configure it.',
                            parent=self,
                        )
        except Exception:
            pass
                # Persist all staged settings on final page (collected from all pages)
        if self._current_page == self._page_count - 1 and self._settings is not None:
            try:
                # Save settings from distributed pages:
                # Page 1: Connect on Startup (and suppress prompts when enabled)
                if hasattr(self, '_connect_var'):
                    self._settings.connect_on_startup = bool(self._connect_var.get())
                    try:
                        if self._settings.connect_on_startup and hasattr(self._settings, 'prompt_for_connect_on_startup'):
                            self._settings.prompt_for_connect_on_startup = False
                    except Exception:
                        pass
                # Page 2: Auto-search clipboard after connect  
                if hasattr(self, '_auto_search_after_var'):
                    self._settings.auto_search_clipboard_after_connect = bool(self._auto_search_after_var.get())
                # Page 3: Open root folder on SKU found
                if hasattr(self, '_open_root_var'):
                    self._settings.open_root_on_sku_found = bool(self._open_root_var.get())
                # Page 5: Auto-load multiple SKUs
                if hasattr(self, '_auto_load_multi_var'):
                    self._settings.auto_load_multi_skus_without_prompt = bool(self._auto_load_multi_var.get())
                # Page 7: Sounds On only (Prompt to connect removed as requested)
                if hasattr(self, '_sounds_var'):
                    self._settings.sounds_enabled = bool(self._sounds_var.get())
                # Page 7: Show Welcome on Startup
                if hasattr(self, '_show_welcome_var'):
                    self._settings.show_help_on_startup = bool(self._show_welcome_var.get())
                
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
        # If we're on page 0 and the Connect button exists, update its appearance
        if self._current_page == 0:
            self.after(10, self._update_connect_button_appearance)  # Small delay to ensure button is created
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
        if p not in (0, 1, 2, 3, 4, 5, 6):
            return
        for _ in range(2):
            ttk.Frame(self._extra_frame, height=8).pack(fill='x')
        try:
            if p == 0:
                row = ttk.Frame(self._extra_frame); row.pack()
                ttk.Label(row, text='To begin, we must connect to Google Drive.').pack(side='left')
                
                # Create Connect button and store reference
                is_connected = callable(self._cb_is_connected) and bool(self._cb_is_connected())
                button_text = 'Connected' if is_connected else 'Connect'
                self._connect_button = ttk.Button(row, text=button_text, command=self._on_press_auth)
                self._connect_button.pack(side='left', padx=(12, 0))
                
                # Configure button appearance based on connection status
                self._update_connect_button_appearance()
                
                # Add Connect on Startup checkbox (centered below)
                connect_cb_frame = ttk.Frame(self._extra_frame)
                connect_cb_frame.pack(pady=(8, 0))
                connect_default = True  # Checked in Welcome to set up auto-connect going forward
                self._connect_var = tk.BooleanVar(value=connect_default)
                ttk.Checkbutton(connect_cb_frame, variable=self._connect_var).pack(side='left', padx=(0, 6))
                ttk.Label(connect_cb_frame, text='Connect on Startup').pack(side='left')
            elif p == 1:
                # Add Auto Search clipboard checkbox to page 2 (centered)
                auto_search_cb_frame = ttk.Frame(self._extra_frame)
                auto_search_cb_frame.pack()
                auto_search_default = True  # Default to True in Welcome
                self._auto_search_after_var = tk.BooleanVar(value=auto_search_default)
                ttk.Checkbutton(auto_search_cb_frame, variable=self._auto_search_after_var).pack(side='left', padx=(0, 6))
                ttk.Label(auto_search_cb_frame, text='Auto-search clipboard after connect').pack(side='left')
            elif p == 2:
                # Add Auto open root checkbox to page 3 (centered)
                auto_open_cb_frame = ttk.Frame(self._extra_frame)
                auto_open_cb_frame.pack()
                auto_open_default = False  # Default to False
                self._open_root_var = tk.BooleanVar(value=auto_open_default)
                ttk.Checkbutton(auto_open_cb_frame, variable=self._open_root_var).pack(side='left', padx=(0, 6))
                ttk.Label(auto_open_cb_frame, text='Open root folder on SKU found').pack(side='left')
            elif p == 3:
                row = ttk.Frame(self._extra_frame); row.pack()
                ttk.Label(row, text='You can set your favorite shortcuts in the settings now, or press F11 later.').pack(side='left')
                ttk.Button(row, text='Set Favorites', command=self._on_press_open_settings).pack(side='left', padx=(12, 0))
            elif p == 4:
                # Add Auto load multiple checkbox to page 5 (centered)
                auto_load_cb_frame = ttk.Frame(self._extra_frame)
                auto_load_cb_frame.pack()
                auto_load_default = False  # Default to False
                self._auto_load_multi_var = tk.BooleanVar(value=auto_load_default)
                ttk.Checkbutton(auto_load_cb_frame, variable=self._auto_load_multi_var).pack(side='left', padx=(0, 6))
                ttk.Label(auto_load_cb_frame, text='Auto-load multiple SKUs (no prompt)').pack(side='left')
            elif p == 5:
                ttk.Label(self._extra_frame, text='Choose your Working Folder, where you keep your projects:').pack(anchor='w')
                browse = ttk.Frame(self._extra_frame); browse.pack(fill='x', pady=(4, 0))
                # Get current working folder from settings, display current path if already set
                current = '' if not self._settings else (self._settings.working_folder or '')
                if current:
                    # Show current path with better formatting
                    display_text = f'Current: {current}'
                else:
                    display_text = '(no folder selected)'
                self._wf_var = tk.StringVar(value=display_text)
                self._wf_entry = ttk.Entry(browse, textvariable=self._wf_var, width=54, state='readonly')
                self._wf_entry.pack(side='left', padx=(0, 6))
                ttk.Button(browse, text='Browse…', command=self._pick_working_folder).pack(side='left')
                # Store the actual path separately for validation
                self._actual_wf_path = current
            elif p == 6:
                # Page 7: Final settings page with remaining controls (Sounds + Show Welcome)
                # Initialize variables for any controls not yet created on other pages
                if not hasattr(self, '_sounds_var'):
                    sounds_default = True
                    self._sounds_var = tk.BooleanVar(value=sounds_default)
                
                # Center the Sounds control on page 7
                sounds_cb_frame = ttk.Frame(self._extra_frame)
                sounds_cb_frame.pack()
                ttk.Checkbutton(sounds_cb_frame, variable=self._sounds_var).pack(side='left', padx=(0, 6))
                ttk.Label(sounds_cb_frame, text='Sounds On').pack(side='left')

                # Show Welcome on Startup toggle
                for _ in range(1):
                    ttk.Frame(self._extra_frame, height=8).pack(fill='x')
                show_welcome_frame = ttk.Frame(self._extra_frame)
                show_welcome_frame.pack()
                default_sw = True if self._settings is None else bool(getattr(self._settings, 'show_help_on_startup', True))
                self._show_welcome_var = tk.BooleanVar(value=default_sw)
                ttk.Checkbutton(show_welcome_frame, variable=self._show_welcome_var).pack(side='left', padx=(0, 6))
                ttk.Label(show_welcome_frame, text='Show Welcome Window on Startup').pack(side='left')

                # Add Home key instruction
                for _ in range(2):
                    ttk.Frame(self._extra_frame, height=8).pack(fill='x')
                
                home_key_frame = ttk.Frame(self._extra_frame)
                home_key_frame.pack()
                ttk.Label(
                    home_key_frame, 
                    text='💡 Tip: Press Home key anytime to reopen this Welcome Window',
                    font=('TkDefaultFont', 10, 'italic')
                ).pack()
        except Exception:
            pass
        for _ in range(2):
            ttk.Frame(self._extra_frame, height=8).pack(fill='x')

    # ---------- Actions ----------
    def _on_press_auth(self) -> None:
        if callable(self._cb_auth_connect):
            try:
                self._cb_auth_connect()
                # Update button appearance after successful connection
                self._update_connect_button_appearance()
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

    def refresh_connection_status(self) -> None:
        """Refresh the connection status and update UI accordingly.
        
        This method can be called from external sources when the connection
        status changes to update the welcome window's UI.
        """
        if self._current_page == 0:  # Only update if we're on the connect page
            self._update_connect_button_appearance()
    
    def _update_connect_button_appearance(self) -> None:
        """Update Connect button appearance based on connection status."""
        if not hasattr(self, '_connect_button'):
            return
        
        try:
            is_connected = callable(self._cb_is_connected) and bool(self._cb_is_connected())
            
            if is_connected:
                # Change to green "Connected" state
                self._connect_button.configure(text='Connected')
                
                # For reliable green styling, always use tk.Button on macOS/darwin
                # ttk styling is too limited on native macOS themes
                styling_success = False
                
                # Check if we're on macOS or if we want to force tk.Button for green styling
                use_tk_button = (sys.platform == 'darwin') or True  # Force tk.Button for reliable styling
                
                if not use_tk_button:
                    # Approach 1: Try ttk styling first (for non-macOS platforms)
                    try:
                        style = ttk.Style()
                        style_name = 'Connected.TButton'
                        
                        style.configure(
                            style_name,
                            background='#28a745',
                            foreground='white',
                            focuscolor='none',
                            relief='raised',
                            borderwidth=1
                        )
                        style.map(
                            style_name,
                            background=[('active', '#218838'), ('pressed', '#1e7e34')],
                            foreground=[('active', 'white'), ('pressed', 'white')],
                            relief=[('pressed', 'sunken')]
                        )
                        
                        self._connect_button.configure(style=style_name)
                        styling_success = True
                        
                    except Exception as e:
                        print(f"TTK styling failed: {e}")
                
                # Approach 2: Use tk.Button for reliable cross-platform green styling
                if not styling_success and hasattr(self, '_connect_button'):
                    try:
                        # Get the parent and position of the current button
                        parent = self._connect_button.master
                        pack_info = self._connect_button.pack_info()
                        
                        # Remove the old ttk button
                        self._connect_button.destroy()
                        
                        # Create a new tk.Button with direct color control
                        self._connect_button = tk.Button(
                            parent,
                            text='Connected',
                            command=self._on_press_auth,
                            bg='#2b2b2b',    # Dark gray background
                            fg='#28a745',    # Green text
                            activebackground='#3a3a3a',  # Slightly lighter gray when hovered
                            activeforeground='#22c55e',  # Brighter green text when hovered
                            relief='raised',
                            borderwidth=1,
                            font=('Segoe UI', 9) if sys.platform == 'win32' else None
                        )
                        
                        # Restore the same packing
                        self._connect_button.pack(**pack_info)
                        
                        styling_success = True
                        
                    except Exception as e:
                        print(f"tk.Button replacement failed: {e}")
                
                if not styling_success:
                    print("Warning: Could not apply green styling to Connect button")
                    
            else:
                # Reset to default "Connect" state
                # If we have a tk.Button (green state), replace with ttk.Button
                if hasattr(self, '_connect_button') and isinstance(self._connect_button, tk.Button):
                    try:
                        # Get the parent and position
                        parent = self._connect_button.master
                        pack_info = self._connect_button.pack_info()
                        
                        # Remove the tk button
                        self._connect_button.destroy()
                        
                        # Create new ttk button
                        self._connect_button = ttk.Button(
                            parent,
                            text='Connect',
                            command=self._on_press_auth
                        )
                        
                        # Restore packing
                        self._connect_button.pack(**pack_info)
                        
                    except Exception:
                        pass
                else:
                    # Just update text and reset style
                    self._connect_button.configure(text='Connect')
                    try:
                        self._connect_button.configure(style='TButton')
                    except Exception:
                        pass
                
                try:
                    self._connect_button.configure(state='normal')
                except Exception:
                    pass
                    
        except Exception as e:
            print(f"Connect button appearance update failed: {e}")
            pass

    def _pick_working_folder(self) -> None:
        # Use the actual path stored separately, not the display text
        current = getattr(self, '_actual_wf_path', '') or ''
        try:
            chosen = filedialog.askdirectory(
                parent=self, 
                initialdir=current or None, 
                title='Select Working Folder'
            )
        except Exception:
            chosen = ''
        
        if chosen:
            try:
                # Validate the chosen directory exists
                chosen_path = Path(chosen)
                if not chosen_path.exists() or not chosen_path.is_dir():
                    messagebox.showerror(
                        title='Invalid Folder',
                        message=f'The selected path is not a valid directory:\n{chosen}',
                        parent=self
                    )
                    return
                
                # Update the display and internal state
                self._wf_entry.configure(state='normal')
                self._wf_var.set(f'Current: {chosen}')
                self._wf_entry.configure(state='readonly')
                self._actual_wf_path = chosen
                
                # Save to settings if different from current setting
                if self._settings is not None:
                    old_path = (self._settings.working_folder or '').strip()
                    if old_path != chosen:
                        self._settings.working_folder = chosen
                        if callable(self._cb_save_settings):
                            self._cb_save_settings()
                        # Log the change
                        print(f'Working folder updated: {old_path} -> {chosen}')
                        
            except Exception as e:
                messagebox.showerror(
                    title='Error',
                    message=f'Error setting working folder: {str(e)}',
                    parent=self
                )
                print(f'Error in _pick_working_folder: {e}')

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
