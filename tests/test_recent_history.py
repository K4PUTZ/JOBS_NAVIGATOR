"""Tests for recent SKU history."""

from sofa_jobs_navigator.config.settings import Favorite, Settings
from sofa_jobs_navigator.services.recent_history import RecentSKUHistory


def make_settings(recents=None):
    return Settings(favorites=[Favorite(label='Test', path='')], recent_skus=recents or [])


def test_add_and_dedupe():
    settings = make_settings()
    history = RecentSKUHistory(settings)
    history.add('SKU1')
    history.add('SKU2')
    history.add('SKU1')
    assert history.items() == ['SKU1', 'SKU2']
    assert settings.recent_skus == ['SKU1', 'SKU2']


def test_clear():
    settings = make_settings(['SKU1'])
    history = RecentSKUHistory(settings)
    history.clear()
    assert history.items() == []
    assert settings.recent_skus == []
