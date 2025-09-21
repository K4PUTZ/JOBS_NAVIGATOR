"""Recent SKU history manager."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Deque, Iterable, List

from ..config.settings import Settings

MAX_RECENTS = 10


@dataclass
class RecentSKUHistory:
    settings: Settings

    def __post_init__(self) -> None:
        self._items: Deque[str] = deque(self.settings.recent_skus, maxlen=MAX_RECENTS)

    def add(self, sku: str) -> None:
        if not sku:
            return
        if sku in self._items:
            self._items.remove(sku)
        self._items.appendleft(sku)
        self.settings.recent_skus = list(self._items)

    def items(self) -> List[str]:
        return list(self._items)

    def clear(self) -> None:
        self._items.clear()
        self.settings.recent_skus = []


# =================== END RECENT HISTORY ===================
