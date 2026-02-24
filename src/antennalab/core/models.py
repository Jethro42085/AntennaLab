from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable


@dataclass(frozen=True)
class ScanBin:
    freq_hz: float
    avg_db: float
    max_db: float


@dataclass(frozen=True)
class ScanResult:
    timestamp: str
    start_hz: float
    stop_hz: float
    bin_hz: float
    bins: tuple[ScanBin, ...]
    antenna_tag: str | None = None
    location_tag: str | None = None

    @staticmethod
    def now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    def iter_bins(self) -> Iterable[ScanBin]:
        return self.bins
