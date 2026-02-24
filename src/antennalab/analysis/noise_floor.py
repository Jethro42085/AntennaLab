from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from antennalab.core.models import ScanBin
from antennalab.report.export_csv import read_scan_csv, write_noise_floor_csv


@dataclass(frozen=True)
class NoiseFloorBin:
    freq_hz: float
    noise_floor_db: float


@dataclass(frozen=True)
class NoiseFloorResult:
    source_scan: Path
    bins: tuple[NoiseFloorBin, ...]


class NoiseFloorEstimator:
    def __init__(self, strategy: str = "avg") -> None:
        self.strategy = strategy

    def estimate(self, scan_bins: list[ScanBin]) -> NoiseFloorResult:
        if self.strategy != "avg":
            raise ValueError(f"unsupported strategy: {self.strategy}")
        bins = tuple(
            NoiseFloorBin(freq_hz=bin_.freq_hz, noise_floor_db=bin_.avg_db)
            for bin_ in scan_bins
        )
        return NoiseFloorResult(source_scan=Path(""), bins=bins)


def estimate_noise_floor(
    scan_csv: str | Path,
    out_csv: str | Path,
    strategy: str = "avg",
) -> Path:
    scan_meta, scan_bins = read_scan_csv(scan_csv)
    estimator = NoiseFloorEstimator(strategy=strategy)
    result = estimator.estimate(scan_bins)
    return write_noise_floor_csv(
        result,
        out_csv,
        scan_meta=scan_meta,
        strategy=strategy,
    )
