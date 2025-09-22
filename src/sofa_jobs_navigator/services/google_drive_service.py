"""Google Drive API-backed service implementing DriveServiceProtocol."""

from __future__ import annotations

from typing import Optional, Sequence

try:  # Lazy import guard; tests can still run without these packages installed
    from googleapiclient.discovery import build  # type: ignore
except Exception:  # pragma: no cover
    build = None  # type: ignore

from .drive_client import DriveServiceProtocol


FOLDER_MIME = "application/vnd.google-apps.folder"


class GoogleDriveService(DriveServiceProtocol):
    """Concrete Drive service using the Google Drive v3 API."""

    def __init__(self, credentials) -> None:
        if build is None:
            raise RuntimeError("Google client libraries are not installed")
        # cache_discovery=False prevents HTTP cache warnings in some environments
        self._svc = build("drive", "v3", credentials=credentials, cache_discovery=False)

    def find_sku_root(self, sku: str, shared_drive_id: str) -> Optional[str]:
        """Find a top-level folder named exactly as the SKU under the shared drive root."""

        q = (
            f"name = '{sku}' and mimeType = '{FOLDER_MIME}' and '{shared_drive_id}' in parents"
        )
        resp = self._svc.files().list(
            q=q,
            corpora="drive",
            driveId=shared_drive_id,
            includeItemsFromAllDrives=True,
            supportsAllDrives=True,
            fields="files(id,name)",
            pageSize=10,
        ).execute()
        files = resp.get("files", [])
        if not files:
            return None
        return files[0]["id"]

    def resolve_relative_path(
        self, *, shared_drive_id: str, parent_id: str, segments: Sequence[str]
    ) -> Optional[str]:
        """Walk the folder tree by name from ``parent_id`` for each segment."""

        current = parent_id
        for seg in segments:
            seg = seg.strip()
            if not seg:
                continue
            q = f"name = '{seg}' and mimeType = '{FOLDER_MIME}' and '{current}' in parents"
            resp = self._svc.files().list(
                q=q,
                corpora="drive",
                driveId=shared_drive_id,
                includeItemsFromAllDrives=True,
                supportsAllDrives=True,
                fields="files(id,name)",
                pageSize=10,
            ).execute()
            files = resp.get("files", [])
            if not files:
                return None
            current = files[0]["id"]
        return current

    def ensure_child_folder(
        self, *, shared_drive_id: str, parent_id: str, name: str
    ) -> Optional[str]:
        name = (name or "").strip()
        if not name:
            return None
        # First try to find existing
        q = f"name = '{name}' and mimeType = '{FOLDER_MIME}' and '{parent_id}' in parents"
        resp = self._svc.files().list(
            q=q,
            corpora="drive",
            driveId=shared_drive_id,
            includeItemsFromAllDrives=True,
            supportsAllDrives=True,
            fields="files(id,name)",
            pageSize=10,
        ).execute()
        files = resp.get("files", [])
        if files:
            return files[0]["id"]
        # Create if missing
        body = {
            "name": name,
            "mimeType": FOLDER_MIME,
            "parents": [parent_id],
            "driveId": shared_drive_id,
        }
        created = self._svc.files().create(
            body=body,
            fields="id",
            supportsAllDrives=True,
        ).execute()
        return created.get("id")
