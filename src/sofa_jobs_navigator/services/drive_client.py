"""Drive client wrapper with testing hooks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Protocol, Sequence

from ..config.flags import FlagSet, FLAGS
from ..config import reference_data as ref

# =================== SERVICE PROTOCOL ===================
# Implement this protocol when wiring real Google Drive APIs. Tests can
# inject light-weight doubles through the ``service_factory`` parameter.
# ---------------------------------------------------------


class DriveServiceProtocol(Protocol):
    """Minimal interface for Drive folder lookups."""

    def find_sku_root(self, sku: str, shared_drive_id: str) -> Optional[str]:
        ...

    def resolve_relative_path(
        self, *, shared_drive_id: str, parent_id: str, segments: Sequence[str]
    ) -> Optional[str]:
        ...

    def ensure_child_folder(
        self, *, shared_drive_id: str, parent_id: str, name: str
    ) -> Optional[str]:
        """Return ID of a child folder with ``name`` under ``parent_id``; create if missing.

        Should be idempotent: if a folder already exists with the exact name, return its ID.
        """
        ...


@dataclass
class DriveLookupResult:
    """Represents the outcome of a Drive lookup."""

    sku: str
    shared_drive_id: str
    folder_id: str
    path: str


# =================== DRIVE CLIENT ===================
# High-level helper that handles shared-drive routing and path traversal.
# Respect ``FLAGS.offline_mode`` to avoid live API calls during tests.
# ----------------------------------------------------


class DriveClient:
    """Facade around Drive folder operations."""

    def __init__(
        self,
        *,
        flags: FlagSet = FLAGS,
        service_factory: Optional[callable] = None,
        logger: Optional[callable] = None,
    ) -> None:
        self._flags = flags
        self._logger = logger
        self._service_factory = service_factory
        self._service: Optional[DriveServiceProtocol] = None

    # =================== PRIMARY OPERATIONS ===================
    def shared_drive_for_sku(self, sku: str) -> str:
        """Return the shared drive ID responsible for *sku*."""

        if not sku:
            raise ValueError("SKU is required")
        first = sku.strip()[0].upper()
        for key, drive_id in ref.SHARED_DRIVE_IDS.items():
            start, end = key.split('-')
            if start <= first <= end:
                self._debug(f"SKU {sku}: mapped to drive {drive_id}")
                return drive_id
        raise ValueError(f"No shared drive mapping for SKU starting with '{first}'")

    def locate_root_folder(self, sku: str) -> DriveLookupResult:
        """Locate the SKU root folder, respecting offline mode."""

        shared_drive = self.shared_drive_for_sku(sku)
        if self._flags.offline_mode or self._service_factory is None:
            folder_id = f"offline:{sku}"
            self._debug(f"Offline locate root => {folder_id}")
            return DriveLookupResult(sku=sku, shared_drive_id=shared_drive, folder_id=folder_id, path="")

        service = self._get_service()
        folder_id = service.find_sku_root(sku, shared_drive)
        if not folder_id:
            raise LookupError(f"Drive root not found for SKU '{sku}'")
        self._debug(f"Located real root folder {folder_id}")
        return DriveLookupResult(sku=sku, shared_drive_id=shared_drive, folder_id=folder_id, path="")

    def resolve_relative_path(self, sku: str, relative_path: str) -> DriveLookupResult:
        """Resolve a relative path under the SKU root.

        Returns a :class:`DriveLookupResult` representing the final folder.
        """

        root = self.locate_root_folder(sku)
        if not relative_path:
            return root

        segments = [seg for seg in relative_path.split('/') if seg]
        if not segments:
            return root

        if self._flags.offline_mode or self._service_factory is None:
            folder_id = '/'.join([root.folder_id, *segments])
            path = '/'.join(segments)
            self._debug(f"Offline resolve path => {folder_id}")
            return DriveLookupResult(
                sku=sku,
                shared_drive_id=root.shared_drive_id,
                folder_id=folder_id,
                path=path,
            )

        service = self._get_service()
        folder_id = service.resolve_relative_path(
            shared_drive_id=root.shared_drive_id,
            parent_id=root.folder_id,
            segments=segments,
        )
        if not folder_id:
            raise LookupError(f"Could not resolve path '{relative_path}' for SKU '{sku}'")
        return DriveLookupResult(
            sku=sku,
            shared_drive_id=root.shared_drive_id,
            folder_id=folder_id,
            path='/'.join(segments),
        )

    def create_child_folder(self, sku: str, parent_relative_path: Optional[str], name: str) -> DriveLookupResult:
        """Create (or get) a child folder named ``name`` under the given relative path.

        When offline, returns a synthetic folder ID incorporating the path.
        """
        if not name:
            raise ValueError("Folder name is required")
        # Locate parent
        parent_path = (parent_relative_path or '').strip().strip('/')
        parent = self.resolve_relative_path(sku, parent_path)

        # Offline behavior: synthesize an ID and path
        if self._flags.offline_mode or self._service_factory is None:
            full_path = '/'.join(filter(None, [parent.path, name]))
            folder_id = f"{parent.folder_id}/{name}"
            self._debug(f"Offline ensure folder => {folder_id}")
            return DriveLookupResult(
                sku=sku,
                shared_drive_id=parent.shared_drive_id,
                folder_id=folder_id,
                path=full_path,
            )

        # Online: ensure/create via service
        service = self._get_service()
        folder_id = service.ensure_child_folder(
            shared_drive_id=parent.shared_drive_id,
            parent_id=parent.folder_id,
            name=name,
        )
        if not folder_id:
            raise LookupError(f"Failed to create or locate folder '{name}' under '{parent.path or '/'}'")
        full_path = '/'.join(filter(None, [parent.path, name]))
        return DriveLookupResult(
            sku=sku,
            shared_drive_id=parent.shared_drive_id,
            folder_id=folder_id,
            path=full_path,
        )

    # =================== INTERNAL HELPERS ===================
    def _get_service(self) -> DriveServiceProtocol:
        if self._service is None:
            if self._service_factory is None:
                raise RuntimeError("Drive service factory not provided")
            self._service = self._service_factory()
        return self._service

    def _debug(self, message: str) -> None:
        if not self._flags.verbose_logging:
            return
        if self._logger:
            self._logger(message)
        else:
            print(message)


# =================== END DRIVE CLIENT ===================
