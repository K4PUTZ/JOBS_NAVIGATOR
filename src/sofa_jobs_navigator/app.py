"""Application entrypoint for Sofa Jobs Navigator."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox
import os
import subprocess
import webbrowser
import sys

from .config.flags import FLAGS
from .version import app_display_title
from .config.settings import Settings, SettingsManager
from .controls.hotkeys import HotkeyManager
from .logging.event_log import LOGGER
from .services.auth_service import AuthService
from .services.drive_client import DriveClient
from .services.recent_history import RecentSKUHistory
from .services.google_drive_service import GoogleDriveService
from .ui.main_window import MainWindow
from .ui.about_window import AboutWindow
from .ui.welcome_window import WelcomeWindow
from .ui.settings_dialog import SettingsDialog
from .utils.app_icons import set_app_icon
from .utils.clipboard import ClipboardReader
from .utils.sku import DEFAULT_DETECTOR
from .utils.sound import SoundPlayer


# =================== APPLICATION BOOT ===================

def run() -> None:
    settings_manager = SettingsManager()
    settings = settings_manager.load()
    recent_history = RecentSKUHistory(settings)
    last_sku: str | None = None

    root = tk.Tk()
    root.title(app_display_title())
    root.geometry('1100x820')
    # Apply app icon (best-effort)
    try:
        set_app_icon(root)
    except Exception:
        pass
    # Center main window on screen
    try:
        root.update_idletasks()
        w = 1100
        h = 820
        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        x = max((sw // 2) - (w // 2), 0)
        y = max((sh // 2) - (h // 2), 0)
        root.geometry(f"{w}x{h}+{x}+{y}")
    except Exception:
        pass

    auth_service = AuthService()
    drive_client = DriveClient()
    clipboard = ClipboardReader(tk_root=root)
    sound_player = SoundPlayer()
    # Apply initial sound setting
    try:
        sound_player.set_enabled(bool(getattr(settings, 'sounds_enabled', True)))
    except Exception:
        pass
    current_account: str | None = None

    def update_account_label(account: str | None) -> None:
        nonlocal current_account
        current_account = account

    def navigate_to_favorite(sku: str, favorite_path: str) -> None:
        if not sku or sku == '(unknown)':
            main_window.console_warning('No SKU context yet. Press F12 after copying a SKU.')
            sound_player.play_warning()
            return
        try:
            result = drive_client.resolve_relative_path(sku, favorite_path)
            LOGGER.info('Resolved path', sku=sku, path=favorite_path, folder_id=result.folder_id)
            main_window.console_success(f"Resolved path '{favorite_path or '(root)'}' -> {result.folder_id}")
            # Build Google Drive URL and open in the default browser
            url = f"https://drive.google.com/drive/folders/{result.folder_id}"
            main_window.console_success(f"Opening in browser: {url}")
            try:
                opened = webbrowser.open(url, new=2)
                if not opened:
                    # Fallback to OS-specific opener
                    if sys.platform == 'darwin':
                        subprocess.run(['open', url], check=False)
                    elif os.name == 'nt':
                        subprocess.run(['start', url], shell=True, check=False)
                    else:
                        subprocess.run(['xdg-open', url], check=False)
            except Exception:
                # Non-fatal; user can still use the URL from the console
                pass
            sound_player.play_success()
        except LookupError as exc:
            main_window.console_error(str(exc))
            LOGGER.warn('Path resolution failed', sku=sku, path=favorite_path)
            sound_player.play_warning()

    def handle_launch(event: tk.Event | None = None) -> None:
        nonlocal last_sku
        text = clipboard.read_text()
        if not FLAGS.offline_mode:
            try:
                creds = auth_service.ensure_authenticated()
                # Prefer real user email when available
                email = auth_service.get_account_email(creds) or getattr(creds, 'service_account_email', None) or getattr(creds, 'client_id', None)
                update_account_label(email)
                # Inject online Drive service for real lookups via factory
                drive_client._service_factory = lambda: GoogleDriveService(creds)  # type: ignore[attr-defined]
                try:
                    expiry = auth_service.get_token_expiry_iso(creds)
                    main_window.set_status(online=True, account=email, token_expiry_iso=expiry)
                except Exception:
                    pass
            except Exception as exc:
                main_window.console_error(f'Auth failed: {exc}')
                LOGGER.error('auth.failed', error=str(exc))
                sound_player.play_warning()
                return
        sku_result = DEFAULT_DETECTOR.find_first(text)
        if not sku_result:
            main_window.console_warning('No SKU found in clipboard.')
            LOGGER.warn('SKU missing from clipboard')
            sound_player.play_warning()
            return

        sku = sku_result.sku
        try:
            main_window.console_sku_detected(sku)
        except Exception:
            main_window.append_console(f'SKU detected: {sku}')
        LOGGER.info('SKU detected', sku=sku)

        if settings.save_recent_skus:
            recent_history.add(sku)
            settings_manager.save(settings)
        main_window.update_recents(recent_history.items())
        # No secondary window; use Favorites panel or press F1–F8 to open a favorite
        main_window.console_success('Choose a Favorite on the right (or press F1–F8).')
        last_sku = sku
        try:
            main_window.set_current_sku(sku)
            main_window.set_favorites_enabled(True)
        except Exception:
            pass
        # Optionally open the root folder of the SKU when setting is enabled
        try:
            if bool(getattr(settings, 'open_root_on_sku_found', False)):
                # Resolve root path and open in browser (same as navigate_to_favorite with empty path)
                try:
                    result = drive_client.resolve_relative_path(sku, '')
                    url = f"https://drive.google.com/drive/folders/{result.folder_id}"
                    main_window.console_success(f"Opening SKU root in browser: {url}")
                    try:
                        opened = webbrowser.open(url, new=2)
                        if not opened:
                            if sys.platform == 'darwin':
                                subprocess.run(['open', url], check=False)
                            elif os.name == 'nt':
                                subprocess.run(['start', url], shell=True, check=False)
                            else:
                                subprocess.run(['xdg-open', url], check=False)
                    except Exception:
                        pass
                except Exception:
                    pass
        except Exception:
            pass

    def on_create_sku_folder(suffix: str) -> None:
        """Create a local folder under the configured Working Folder named 'SKU + suffix'."""
        # Gather current SKU
        sku = main_window.get_current_sku()
        if not sku:
            main_window.console_warning('No SKU set. Press F12 after copying a SKU.')
            try:
                sound_player.play_warning()
            except Exception:
                pass
            return
        # Resolve working folder from settings
        base_dir = (getattr(settings, 'working_folder', None) or '').strip()
        if not base_dir:
            main_window.console_warning('Working Folder is not set. Open Settings and choose a local folder.')
            try:
                sound_player.play_warning()
            except Exception:
                pass
            return
        # Sanitize folder name slightly for filesystem
        raw_name = f"{sku}{suffix or ''}"
        name = ''.join(ch for ch in raw_name if ch not in '\\/:*?"<>|')
        try:
            from pathlib import Path
            path = Path(base_dir) / name
            path.mkdir(parents=True, exist_ok=True)
            main_window.console_success(f"Created local folder: {path}")
            # Update Working Folder label to reflect settings value (already shown) and play sound
            try:
                sound_player.play_success()
            except Exception:
                pass
            # Open in system file browser
            try:
                if sys.platform == 'darwin':
                    subprocess.run(['open', str(path)], check=False)
                elif os.name == 'nt':
                    subprocess.run(['explorer', str(path)], shell=True, check=False)
                else:
                    subprocess.run(['xdg-open', str(path)], check=False)
            except Exception:
                pass
        except Exception as exc:
            main_window.console_error(f"Create local folder failed: {exc}")
            try:
                sound_player.play_warning()
            except Exception:
                pass

    def on_open_settings() -> None:
        nonlocal settings, recent_history, last_sku, current_account
        dialog_ref: dict[str, SettingsDialog | None] = {"dlg": None}

        def on_save(updated: Settings) -> None:
            nonlocal settings, recent_history
            settings = updated
            settings_manager.save(settings)
            recent_history = RecentSKUHistory(settings)
            main_window.refresh_favorites(settings)
            main_window.update_recents(recent_history.items())
            # Reflect working folder from saved settings
            try:
                main_window.set_working_folder(settings.working_folder)
            except Exception:
                pass
            # Apply toggles immediately
            try:
                sound_player.set_enabled(bool(getattr(settings, 'sounds_enabled', True)))
            except Exception:
                pass
            LOGGER.info('Settings saved via dialog')

        def on_auth_connect() -> None:
            try:
                creds = auth_service.ensure_authenticated()
                email = auth_service.get_account_email(creds) or getattr(creds, 'service_account_email', None) or getattr(creds, 'client_id', None)
                update_account_label(email)
                # Enable online Drive service immediately
                drive_client._service_factory = lambda: GoogleDriveService(creds)  # type: ignore[attr-defined]
                main_window.console_success('Connected to Google Drive.')
                try:
                    expiry = auth_service.get_token_expiry_iso(creds)
                    main_window.set_status(online=True, account=email, token_expiry_iso=expiry)
                except Exception:
                    pass
                # Update account label in settings dialog immediately if open
                try:
                    dlg = dialog_ref.get("dlg")
                    if dlg is not None:
                        dlg.set_account(email)
                except Exception:
                    pass
                LOGGER.info('auth.connected', account=email)
            except Exception as exc:
                main_window.console_error(f'Auth failed: {exc}')
                LOGGER.error('auth.failed', error=str(exc))

        def on_auth_clear() -> None:
            auth_service.clear_tokens()
            update_account_label(None)
            main_window.console_success('Cleared stored credentials.')
            try:
                main_window.set_status(online=False, account=None)
            except Exception:
                pass
            # Update account label in settings dialog immediately if open
            try:
                dlg = dialog_ref.get("dlg")
                if dlg is not None:
                    dlg.set_account(None)
            except Exception:
                pass
            LOGGER.info('auth.cleared')

        dialog_ref["dlg"] = SettingsDialog(
            root,
            settings=settings,
            on_save=on_save,
            on_auth_connect=on_auth_connect,
            on_auth_clear=on_auth_clear,
            current_account=current_account,
        )
        # Ensure we release the dialog reference when it is destroyed
        try:
            dialog_ref["dlg"].bind("<Destroy>", lambda e: dialog_ref.__setitem__("dlg", None))
        except Exception:
            pass

    def on_check_clipboard_action() -> None:
        # Output SKU detection results into the UI console
        txt = clipboard.read_text()
        results = DEFAULT_DETECTOR.find_all(txt or '')
        try:
            main_window.append_console('--- Clipboard SKU scan ---')
            if not results:
                main_window.console_warning('No SKU found.')
                try:
                    sound_player.play_warning()
                except Exception:
                    pass
            else:
                for r in results:
                    try:
                        main_window.append_console_highlight(
                            f"SKU: {r.sku}  @[{r.start}:{r.end}]  context='{r.context}'",
                            highlight=r.sku,
                            highlight_tag='sku'
                        )
                    except Exception:
                        main_window.append_console(f"SKU: {r.sku}  @[{r.start}:{r.end}]  context='{r.context}'")
                try:
                    sound_player.play_success()
                except Exception:
                    pass
        except Exception:
            pass

    def on_search_action() -> None:
        # Invoke the same logic as the F12 launcher
        handle_launch(None)

    def on_about_action() -> None:
        try:
            AboutWindow(root)
        except Exception:
            try:
                main_window.append_console('About dialog is under development.')
            except Exception:
                pass

    def on_help_action() -> None:
        try:
            WelcomeWindow(root)
        except Exception:
            try:
                main_window.append_console('Help is under development.')
            except Exception:
                pass

    def _prompt_connect_setup() -> None:
        """Ask the user if they want to open Help after auto-connect failure.

        Includes a 'Don't show again' checkbox tied to settings.suppress_connect_setup_prompt
        and the Reset warnings button in Settings.
        """
        try:
            # Build a custom dialog to include a checkbox
            dlg = tk.Toplevel(root)
            dlg.title('Setup Google Drive?')
            dlg.transient(root)
            dlg.grab_set()
            try:
                set_app_icon(dlg)
            except Exception:
                pass
            frm = tk.Frame(dlg, padx=12, pady=12)
            frm.pack(fill='both', expand=True)
            msg = tk.Label(
                frm,
                text='It looks like you are not connected to Google Drive,\nwould you like to set up the program now?'
            )
            msg.pack(anchor='w')
            dont_var = tk.BooleanVar(value=False)
            chk = tk.Checkbutton(frm, text="Don't show again", variable=dont_var)
            chk.pack(anchor='w', pady=(8, 0))
            btns = tk.Frame(frm)
            btns.pack(fill='x', pady=(12, 0))
            result = {'ok': False}

            def on_yes():
                result['ok'] = True
                dlg.destroy()

            def on_no():
                result['ok'] = False
                dlg.destroy()

            tk.Button(btns, text='Yes', command=on_yes).pack(side='right')
            tk.Button(btns, text='No', command=on_no).pack(side='right', padx=(0, 6))

            # Center the dialog
            try:
                dlg.update_idletasks()
                w = dlg.winfo_width() or dlg.winfo_reqwidth()
                h = dlg.winfo_height() or dlg.winfo_reqheight()
                sw = dlg.winfo_screenwidth()
                sh = dlg.winfo_screenheight()
                x = max((sw // 2) - (w // 2), 0)
                y = max((sh // 2) - (h // 2), 0)
                dlg.geometry(f"{w}x{h}+{x}+{y}")
            except Exception:
                pass
            dlg.wait_window()
            # Persist suppression choice if checked
            try:
                if bool(dont_var.get()):
                    setattr(settings, 'suppress_connect_setup_prompt', True)
                    settings_manager.save(settings)
            except Exception:
                pass
            # Open Help when user accepts
            if result['ok']:
                try:
                    WelcomeWindow(root)
                except Exception:
                    pass
        except Exception:
            # Fallback to simple Yes/No without checkbox
            try:
                ok = messagebox.askyesno(
                    title='Setup Google Drive?',
                    message='It looks like you are not connected to Google Drive, would you like to set up the program now?'
                )
                if ok:
                    WelcomeWindow(root)
            except Exception:
                pass

    main_window = MainWindow(
        root,
        settings=settings,
        on_launch_shortcut=lambda path: navigate_to_favorite(last_sku or '(unknown)', path),
        on_open_settings=on_open_settings,
        on_check_clipboard=on_check_clipboard_action,
        on_search=on_search_action,
        on_about=on_about_action,
        on_help=on_help_action,
        on_create_sku_folder=on_create_sku_folder,
        on_settings_change=lambda s: settings_manager.save(s),
    )
    # Ensure window is large enough to accommodate all UI elements
    try:
        root.update_idletasks()
        req_w = root.winfo_reqwidth()
        req_h = root.winfo_reqheight()
        cur_w = root.winfo_width()
        cur_h = root.winfo_height()
        if req_h > cur_h or req_w > cur_w:
            new_w = max(cur_w, req_w)
            new_h = max(cur_h, req_h)
            sw = root.winfo_screenwidth()
            sh = root.winfo_screenheight()
            x = max((sw // 2) - (new_w // 2), 0)
            y = max((sh // 2) - (new_h // 2), 0)
            root.geometry(f"{new_w}x{new_h}+{x}+{y}")
        # Set minimum size so layout doesn't clip if user resizes smaller
        try:
            root.minsize(width=root.winfo_width(), height=root.winfo_height())
        except Exception:
            pass
    except Exception:
        pass
    # Initialize status bar
    try:
        main_window.set_status(online=False, account=None)
    except Exception:
        pass
    # Initialize current SKU and disable favorites until one is detected
    try:
        main_window.set_current_sku(None)
        main_window.set_favorites_enabled(False)
    except Exception:
        pass
    # Reflect Working Folder from settings at startup
    try:
        main_window.set_working_folder(settings.working_folder)
    except Exception:
        pass
    main_window.console_hint('Copy a SKU (Vendor-ID) to the memory and click search or press F12.')
    main_window.update_recents(recent_history.items())
    # No auto-opening Help on startup.

    hotkeys = HotkeyManager(root=root)
    hotkeys.setup_default_shortcuts(lambda event: handle_launch(event))
    # Extra toolbar hotkeys: F9 (check clipboard), F10 (about), F11 (settings)
    try:
        root.bind_all('<F9>', lambda e: on_check_clipboard_action(), add=True)
        root.bind_all('<F10>', lambda e: on_about_action(), add=True)
        root.bind_all('<F11>', lambda e: on_open_settings(), add=True)
        root.bind_all('<Home>', lambda e: on_help_action(), add=True)
    except Exception:
        pass
    # Map numpad 0 to Search (same as F12)
    try:
        root.bind_all('<KP_0>', lambda e: on_search_action(), add=True)
    except Exception:
        pass

    # Attempt to auto-connect ONLY when valid cached credentials exist and user enabled setting
    def _attempt_auto_connect() -> None:
        if FLAGS.offline_mode:
            return
        try:
            if not bool(getattr(settings, 'connect_on_startup', False)):
                LOGGER.info('auth.auto_connect_disabled_by_setting')
                return
        except Exception:
            pass
        # Ensure we have valid cached credentials (non-interactive check)
        if not auth_service.has_valid_credentials():
            LOGGER.info('auth.auto_connect_skipped_no_valid_cached_creds')
            return
        try:
            creds = auth_service.ensure_authenticated()
            email = auth_service.get_account_email(creds) or getattr(creds, 'service_account_email', None) or getattr(creds, 'client_id', None)
            update_account_label(email)
            drive_client._service_factory = lambda: GoogleDriveService(creds)  # type: ignore[attr-defined]
            main_window.console_success('Auto-connected to Google Drive')
            try:
                expiry = auth_service.get_token_expiry_iso(creds)
                main_window.set_status(online=True, account=email, token_expiry_iso=expiry)
            except Exception:
                pass
            LOGGER.info('auth.auto_connected', account=email)
        except Exception:
            LOGGER.info('auth.auto_connect_failed')

    def _startup_auth_flow() -> None:
        """Startup credential check/prompt before attempting auto-connect.

        Behavior:
        - If offline mode: do nothing.
        - If valid cached credentials and user enabled auto-connect: connect automatically.
        - If no valid credentials: prompt user to connect now. On decline, warn in console.
        """
        if FLAGS.offline_mode:
            return
        try:
            if auth_service.has_valid_credentials():
                # Only proceed automatically if user opted in via settings
                if bool(getattr(settings, 'connect_on_startup', False)):
                    _attempt_auto_connect()
                else:
                    LOGGER.info('auth.valid_cached_creds_startup_no_autoconnect')
                return
        except Exception:
            pass
        # No valid credentials; ask user
        try:
            ok = messagebox.askyesno(
                title='Connect to Google Drive?',
                message='You are not connected to Google Drive yet. Connect now?'
            )
        except Exception:
            ok = False
        if ok:
            try:
                creds = auth_service.ensure_authenticated()
                email = auth_service.get_account_email(creds) or getattr(creds, 'service_account_email', None) or getattr(creds, 'client_id', None)
                update_account_label(email)
                drive_client._service_factory = lambda: GoogleDriveService(creds)  # type: ignore[attr-defined]
                main_window.console_success('Connected to Google Drive.')
                try:
                    expiry = auth_service.get_token_expiry_iso(creds)
                    main_window.set_status(online=True, account=email, token_expiry_iso=expiry)
                except Exception:
                    pass
                LOGGER.info('auth.connected.startup_prompt', account=email)
            except Exception as exc:
                main_window.console_error(f'Auth failed: {exc}')
                LOGGER.error('auth.failed.startup_prompt', error=str(exc))
        else:
            main_window.console_warning('Not connected. Press F11 to connect to Google Drive.')
            LOGGER.info('auth.startup_user_declined')

    try:
        # Schedule startup auth decision flow (includes optional auto-connect)
        root.after(250, _startup_auth_flow)
    except Exception:
        pass

    # Additionally, bring up the setup dialog on startup when conditions are met:
    # - working folder is empty
    # - user is not connected
    # - suppression flag is not enabled
    def _maybe_prompt_setup() -> None:
        try:
            wf = (getattr(settings, 'working_folder', None) or '').strip()
        except Exception:
            wf = ''
        try:
            suppressed = bool(getattr(settings, 'suppress_connect_setup_prompt', False))
        except Exception:
            suppressed = False
        # Determine if we're online by checking if a service factory was injected via auth flow
        online = drive_client._service_factory is not None  # type: ignore[attr-defined]
        if not wf and not online and not suppressed:
            _prompt_connect_setup()

    try:
        root.after(500, _maybe_prompt_setup)
    except Exception:
        pass

    root.mainloop()


# =================== END APPLICATION BOOT ===================


if __name__ == '__main__':
    run()

