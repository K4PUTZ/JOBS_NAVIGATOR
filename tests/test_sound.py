"""Sound player tests."""

from unittest import mock

from sofa_jobs_navigator.config.flags import FlagSet
from sofa_jobs_navigator.utils.sound import SoundPlayer


def make_flags(*, mute=False):
    return FlagSet(
        verbose_logging=False,
        offline_mode=False,
        config_dry_run=False,
        ui_debug=False,
        mute_sounds=mute,
        mock_clipboard=None,
        test_hotkey=None,
    )


def test_mute_skips_subprocess(monkeypatch):
    player = SoundPlayer(flags=make_flags(mute=True))
    with mock.patch('subprocess.run') as run_mock:
        player.play_success()
        run_mock.assert_not_called()


def test_play_success_invokes_subprocess(monkeypatch):
    player = SoundPlayer(flags=make_flags())
    monkeypatch.setattr(player, '_system', 'Darwin')
    with mock.patch('subprocess.run') as run_mock:
        player.play_success()
        assert run_mock.called
