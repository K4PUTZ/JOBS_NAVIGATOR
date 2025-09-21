"""Clipboard reader tests."""

from sofa_jobs_navigator.config.flags import FlagSet
from sofa_jobs_navigator.utils.clipboard import ClipboardReader


def make_flags(mock=None):
    return FlagSet(
        verbose_logging=False,
        offline_mode=False,
        config_dry_run=False,
        ui_debug=False,
        mute_sounds=False,
        mock_clipboard=mock,
        test_hotkey=None,
    )


def test_mock_clipboard_overrides():
    reader = ClipboardReader(flags=make_flags(mock='SKU123'))
    assert reader.read_text() == 'SKU123'


def test_tk_root_used_when_no_mock(monkeypatch):
    class Dummy:
        def clipboard_get(self):
            return 'FROM_TK'
    reader = ClipboardReader(flags=make_flags(), tk_root=Dummy())
    assert reader.read_text() == 'FROM_TK'
