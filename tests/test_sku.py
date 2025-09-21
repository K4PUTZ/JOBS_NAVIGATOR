"""Unit tests for SKU detection."""

import pytest

from sofa_jobs_navigator.utils.sku import DEFAULT_DETECTOR


@pytest.mark.parametrize(
    "sample, expected",
    [
        ("Notes MOVIE_2023_TT1234567_M extra", "MOVIE_2023_TT1234567_M"),
        ("line SHOW_NAME_2024_TT12345678_S001_E010", "SHOW_NAME_2024_TT12345678_S001_E010"),
        ("legacy LEGACY_SOFA_20230101_1234 ok", "LEGACY_SOFA_20230101_1234"),
    ],
)
def test_find_first(sample, expected):
    result = DEFAULT_DETECTOR.find_first(sample)
    assert result is not None
    assert result.sku == expected


def test_no_match_returns_none():
    assert DEFAULT_DETECTOR.find_first("no sku here") is None
