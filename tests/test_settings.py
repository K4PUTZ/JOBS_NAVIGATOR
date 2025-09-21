"""Tests for settings persistence."""

from __future__ import annotations

from pathlib import Path

import pytest

from sofa_jobs_navigator.config.flags import FlagSet
from sofa_jobs_navigator.config.settings import Favorite, Settings, SettingsManager


def make_flags(*, dry_run: bool) -> FlagSet:
    return FlagSet(
        verbose_logging=False,
        offline_mode=False,
        config_dry_run=dry_run,
        ui_debug=False,
        mute_sounds=False,
        mock_clipboard=None,
        test_hotkey=None,
    )


def test_defaults_loaded_when_missing(tmp_path: Path):
    manager = SettingsManager(flags=make_flags(dry_run=False), config_dir=tmp_path)
    settings = manager.load()
    # At least 8 favorites should be present by default
    assert len(settings.favorites) >= 8
    assert settings.recent_skus == []


def test_save_and_reload(tmp_path: Path):
    manager = SettingsManager(flags=make_flags(dry_run=False), config_dir=tmp_path)
    custom = Settings(
        favorites=[Favorite(label="Test", path="A/B", hotkey="1")],
        working_folder="/tmp",
        save_recent_skus=False,
        sounds_enabled=False,
        recent_skus=["SKU1", "SKU2"],
    )
    manager.save(custom)
    reloaded = manager.load()
    # Scalar fields should round-trip
    assert reloaded.working_folder == custom.working_folder
    assert reloaded.save_recent_skus == custom.save_recent_skus
    assert reloaded.sounds_enabled == custom.sounds_enabled
    assert reloaded.recent_skus == custom.recent_skus
    # Favorites are padded to a minimum of 8 on load; the saved entries should be preserved at the start
    assert reloaded.favorites[: len(custom.favorites)] == custom.favorites
    assert len(reloaded.favorites) >= len(custom.favorites)


def test_dry_run_skips_write(tmp_path: Path):
    manager = SettingsManager(flags=make_flags(dry_run=True), config_dir=tmp_path)
    original = manager.load()
    manager.save(Settings(favorites=[], working_folder="/tmp", recent_skus=["SKU"]))
    assert not (tmp_path / 'config.json').exists()
