from sofa_jobs_navigator.logging.event_log import EventLogger
from sofa_jobs_navigator.config.flags import FlagSet


def test_debug_respects_flag(tmp_path, monkeypatch):
    flags = FlagSet(
        verbose_logging=False,
        offline_mode=False,
        config_dry_run=False,
        ui_debug=False,
        mute_sounds=False,
        mock_clipboard=None,
        test_hotkey=None,
    )
    logger = EventLogger(flags=flags, log_dir=tmp_path)
    logger.debug("should not appear")
    files = list(tmp_path.iterdir())
    assert len(files) == 1
    assert files[0].read_text() == ""


def test_info_writes_log(tmp_path):
    flags = FlagSet(
        verbose_logging=True,
        offline_mode=False,
        config_dry_run=False,
        ui_debug=False,
        mute_sounds=False,
        mock_clipboard=None,
        test_hotkey=None,
    )
    logger = EventLogger(flags=flags, log_dir=tmp_path)
    logger.info("hello", foo="bar")
    files = list(tmp_path.iterdir())
    assert len(files) == 1
    contents = files[0].read_text()
    assert "hello" in contents
    assert "foo" in contents
