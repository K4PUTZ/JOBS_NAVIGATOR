"""SKU extraction helpers.

All consumers should import :class:`SKUDetector` and reuse it across tools.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, List, Optional

from ..config.flags import FLAGS


# =================== PATTERN DEFINITIONS ===================
# Recognises SKU strings such as:
#   - LEGACY_SOFA_20230101_1234
#   - MOVIE_2023_TT1234567_M
#   - SHOW_NAME_2024_TT12345678_S001_E010
# Adjust ``SKU_PATTERNS`` if new formats appear.
# -----------------------------------------------------------
SKU_PATTERNS: List[re.Pattern[str]] = [
    re.compile(r"[A-Z0-9_]+_SOFA_\d{8}_\d{4}"),
    re.compile(r"[A-Z0-9]+_\d{4}_TT\d{7,8}_M"),
    re.compile(r"[A-Z0-9_]+_\d{4}_TT\d{7,8}_S\d{3}_E\d{3}"),
]


@dataclass
class SKUDetectionResult:
    """Container for a detected SKU instance."""

    sku: str
    start: int
    end: int
    context: str


# =================== SKU DETECTOR ===================
# Provides high-level helpers to find SKUs in arbitrary text blocks.
# Set ``FLAGS.verbose_logging`` to 1 (env ``SJN_VERBOSE``) for step tracing.
# ----------------------------------------------------


class SKUDetector:
    """Searches text blobs for SKU strings.

    Parameters
    ----------
    flags:
        Optional flag set (defaults to global ``FLAGS``) controlling debug output.
    logger:
        Callable accepting a single string, used when verbose logging is enabled.
    """

    def __init__(self, *, flags=FLAGS, logger=None) -> None:
        self._flags = flags
        self._logger = logger

    # -------- SKU VALIDATION ---------
    # Toggle ``FLAGS.verbose_logging`` to see detailed matching info.
    # -------- END VALIDATION ---------
    def find_all(self, text: str) -> List[SKUDetectionResult]:
        """Return every SKU found in *text*.

        The first pattern match wins when SKUs overlap. Results preserve the
        original casing extracted from the text.
        """

        if not text:
            return []

        matches: List[SKUDetectionResult] = []
        for pattern in SKU_PATTERNS:
            for match in pattern.finditer(text):
                sku = match.group(0)
                result = SKUDetectionResult(
                    sku=sku,
                    start=match.start(),
                    end=match.end(),
                    context=text[max(match.start() - 16, 0): match.end() + 16],
                )
                matches.append(result)
                self._debug(f"SKU match @[{result.start}:{result.end}] => {result.sku}")
        return matches

    def find_first(self, text: str) -> Optional[SKUDetectionResult]:
        """Return the first SKU detected in *text*, or ``None`` when absent."""

        for result in self.find_all(text):
            return result
        self._debug("No SKU found in input text")
        return None

    # =================== INTERNALS ===================
    def _debug(self, message: str) -> None:
        if not self._flags.verbose_logging:
            return
        if self._logger:
            self._logger(message)
        else:
            print(message)


DEFAULT_DETECTOR = SKUDetector()

# =================== END SKU DETECTOR ===================
