"""Tests for the DriveClient wrapper."""

from __future__ import annotations

from dataclasses import dataclass

from sofa_jobs_navigator.config.flags import FlagSet
from sofa_jobs_navigator.services.drive_client import DriveClient, DriveLookupResult


def make_flags(*, offline: bool, verbose: bool = False) -> FlagSet:
    return FlagSet(
        verbose_logging=verbose,
        offline_mode=offline,
        config_dry_run=False,
        ui_debug=False,
        mute_sounds=False,
        mock_clipboard=None,
        test_hotkey=None,
    )


def test_shared_drive_routing():
    client = DriveClient(flags=make_flags(offline=True))
    drive_id = client.shared_drive_for_sku("APPLE_2023_TT1234567_M")
    assert drive_id == "0ALFcGfxuw7zqUk9PVA"


def test_offline_locate_and_resolve_path():
    client = DriveClient(flags=make_flags(offline=True))
    root = client.locate_root_folder("MOVIE_2023_TT1234567_M")
    assert root.folder_id == "offline:MOVIE_2023_TT1234567_M"
    target = client.resolve_relative_path("MOVIE_2023_TT1234567_M", "EXPORT/03- ARTES")
    assert target.folder_id.endswith("EXPORT/03- ARTES")


# ------------------ SERVICE DOUBLE ------------------
@dataclass
class StubService:
    root_id: str = "root123"
    resolved: str = "root123/child"

    def find_sku_root(self, sku: str, shared_drive_id: str) -> str:
        return self.root_id

    def resolve_relative_path(self, *, shared_drive_id: str, parent_id: str, segments):
        return self.resolved


def test_online_uses_service():
    stub = StubService()

    def factory():
        return stub

    client = DriveClient(flags=make_flags(offline=False), service_factory=factory)
    root = client.locate_root_folder("MOVIE_2023_TT1234567_M")
    assert root.folder_id == stub.root_id
    target = client.resolve_relative_path("MOVIE_2023_TT1234567_M", "A/B")
    assert target.folder_id == stub.resolved
