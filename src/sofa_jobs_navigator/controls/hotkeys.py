"""Hotkey manager for Sofa Jobs Navigator."""

from __future__ import annotations

import tkinter as tk
from typing import Callable, Dict

from ..config.flags import FlagSet, FLAGS

# =================== HOTKEY MANAGER ===================
# Responsible for binding keyboard shortcuts to callbacks.
# respects ``FLAGS.test_hotkey`` so automated tests can remap the launcher.
# ------------------------------------------------------


class HotkeyManager:
    """Manage Tkinter key bindings for the application."""

    def __init__(self, *, root: tk.Misc, flags: FlagSet = FLAGS) -> None:
        self._root = root
        self._flags = flags
        self._bindings: Dict[str, str] = {}

    # -------- HOTKEY REGISTRATION ---------
    # Use ``register`` for single-action binds. Signature follows Tk expectations.
    # Example: ``register('<F12>', callback)``.
    # -------- END HOTKEY REGISTRATION ---------
    def register(self, sequence: str, callback: Callable[[tk.Event], None]) -> None:
        bind_id = self._root.bind(sequence, callback)
        self._bindings[sequence] = bind_id or ''

    def setup_default_shortcuts(self, launcher: Callable[[tk.Event], None]) -> None:
        """Bind the SKU launcher to F12 (or test override)."""

        sequence = self._flags.test_hotkey or '<F12>'
        self.register(sequence, launcher)

    def clear(self) -> None:
        """Remove all registered bindings."""

        for sequence, bind_id in self._bindings.items():
            if bind_id:
                self._root.unbind(sequence, bind_id)
            else:
                self._root.unbind(sequence)
        self._bindings.clear()


# =================== END HOTKEY MANAGER ===================
