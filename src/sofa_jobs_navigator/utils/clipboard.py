"""Clipboard reader with pyperclip fallback."""

from __future__ import annotations

try:
    import pyperclip  # type: ignore
except Exception:  # pragma: no cover
    pyperclip = None

from ..config.flags import FlagSet, FLAGS


class ClipboardReader:
    def __init__(self, *, flags: FlagSet = FLAGS, tk_root=None) -> None:
        self._flags = flags
        self._tk_root = tk_root

    def read_text(self) -> str:
        if self._flags.mock_clipboard is not None:
            return self._flags.mock_clipboard

        if self._tk_root is not None:
            try:
                tk_clip = self._tk_root.clipboard_get()
                if tk_clip:
                    return tk_clip
            except Exception:
                pass

        if pyperclip is not None:
            try:
                pasted = pyperclip.paste()
                if pasted:
                    return pasted
            except Exception:
                pass

        if self._tk_root is not None:
            try:
                return self._tk_root.clipboard_get() or ''
            except Exception:
                return ''

        return ''


# =================== END CLIPBOARD ===================
