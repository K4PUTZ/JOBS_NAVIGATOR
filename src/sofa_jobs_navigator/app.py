"""Application entrypoint for Sofa Jobs Navigator."""

from __future__ import annotations

import tkinter as tk
import os
import subprocess
import webbrowser
import sys

from .config.flags import FLAGS
from .config.settings import Settings, SettingsManager
from .controls.hotkeys import HotkeyManager
from .logging.event_log import LOGGER
from .services.auth_service import AuthService
from .services.drive_client import DriveClient
from .services.recent_history import RecentSKUHistory
from .services.google_drive_service import GoogleDriveService
from .ui.main_window import MainWindow
from .ui.settings_dialog import SettingsDialog
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
    root.title('Sofa Jobs Navigator 1.0')
    root.geometry('900x600')
    # Center main window on screen
    try:
        root.update_idletasks()
        w = 900
        h = 600
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
    current_account: str | None = None

    def update_account_label(account: str | None) -> None:
        nonlocal current_account
        current_account = account

    def navigate_to_favorite(sku: str, favorite_path: str) -> None:
        if not sku or sku == '(unknown)':
            main_window.append_console('No SKU context yet. Press F12 after copying a SKU.')
            sound_player.play_warning()
            return
        try:
            result = drive_client.resolve_relative_path(sku, favorite_path)
            LOGGER.info('Resolved path', sku=sku, path=favorite_path, folder_id=result.folder_id)
            main_window.append_console(f"Resolved path '{favorite_path or '(root)'}' -> {result.folder_id}")
            # Build Google Drive URL and open in the default browser
            url = f"https://drive.google.com/drive/folders/{result.folder_id}"
            main_window.append_console(f"Opening in browser: {url}")
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
            main_window.append_console(str(exc))
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
                main_window.append_console(f'Auth failed: {exc}')
                LOGGER.error('auth.failed', error=str(exc))
                sound_player.play_warning()
                return
        sku_result = DEFAULT_DETECTOR.find_first(text)
        if not sku_result:
            main_window.append_console('No SKU found in clipboard.')
            LOGGER.warn('SKU missing from clipboard')
            sound_player.play_warning()
            return

        sku = sku_result.sku
        main_window.append_console(f'SKU detected: {sku}')
        LOGGER.info('SKU detected', sku=sku)

        if settings.save_recent_skus:
            recent_history.add(sku)
            settings_manager.save(settings)
        main_window.update_recents(recent_history.items())
        # No secondary window; use Favorites panel or press F1–F8 to open a favorite
        main_window.append_console('Choose a Favorite on the right (or press F1–F8).')
        last_sku = sku
        try:
            main_window.set_current_sku(sku)
            main_window.set_favorites_enabled(True)
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
            LOGGER.info('Settings saved via dialog')

        def on_auth_connect() -> None:
            try:
                creds = auth_service.ensure_authenticated()
                email = auth_service.get_account_email(creds) or getattr(creds, 'service_account_email', None) or getattr(creds, 'client_id', None)
                update_account_label(email)
                # Enable online Drive service immediately
                drive_client._service_factory = lambda: GoogleDriveService(creds)  # type: ignore[attr-defined]
                main_window.append_console('Connected to Google Drive.')
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
                main_window.append_console(f'Auth failed: {exc}')
                LOGGER.error('auth.failed', error=str(exc))

        def on_auth_clear() -> None:
            auth_service.clear_tokens()
            update_account_label(None)
            main_window.append_console('Cleared stored credentials.')
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

    main_window = MainWindow(
        root,
        settings=settings,
        on_launch_shortcut=lambda path: navigate_to_favorite(last_sku or '(unknown)', path),
        on_open_settings=on_open_settings,
    )
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
    main_window.append_console('Copy a SKU (Vendor-ID) to the memory and press F12.')
    main_window.update_recents(recent_history.items())

    hotkeys = HotkeyManager(root=root)
    hotkeys.setup_default_shortcuts(lambda event: handle_launch(event))

    # Attempt to auto-connect on startup (respect offline flag)
    def _attempt_auto_connect() -> None:
        if FLAGS.offline_mode:
            return
        try:
            creds = auth_service.ensure_authenticated()
            email = auth_service.get_account_email(creds) or getattr(creds, 'service_account_email', None) or getattr(creds, 'client_id', None)
            update_account_label(email)
            # Enable online Drive service immediately
            drive_client._service_factory = lambda: GoogleDriveService(creds)  # type: ignore[attr-defined]
            main_window.append_console('Auto-connected to Google Drive')
            try:
                expiry = auth_service.get_token_expiry_iso(creds)
                main_window.set_status(online=True, account=email, token_expiry_iso=expiry)
            except Exception:
                pass
            LOGGER.info('auth.auto_connected', account=email)
        except Exception:
            # Stay silent on failure; user can connect manually
            LOGGER.info('auth.auto_connect_skipped')

    try:
        # Schedule shortly after UI shows to avoid blocking initial render
        root.after(250, _attempt_auto_connect)
    except Exception:
        pass

    root.mainloop()


# =================== END APPLICATION BOOT ===================


if __name__ == '__main__':
    run()
