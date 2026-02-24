from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from antennalab.core.models import ScanBin, ScanResult
from antennalab.report.export_csv import ScanMeta, read_scan_csv


@dataclass(frozen=True)
class Baseline:
    meta: ScanMeta
    bins: tuple[ScanBin, ...]


def load_baseline(path: str | Path) -> Baseline:
    meta, bins = read_scan_csv(path)
    return Baseline(meta=meta, bins=tuple(bins))


def apply_baseline(scan: ScanResult, baseline: Baseline) -> ScanResult:
    _validate_compatible(scan, baseline.meta)
    base_by_freq = {b.freq_hz: b for b in baseline.bins}
    adjusted: list[ScanBin] = []

    for bin_ in scan.bins:
        base = base_by_freq.get(bin_.freq_hz)
        if base is None:
            adjusted.append(bin_)
            continue
        adjusted.append(
            ScanBin(
                freq_hz=bin_.freq_hz,
                avg_db=bin_.avg_db - base.avg_db,
                max_db=bin_.max_db - base.avg_db,
            )
        )

    return ScanResult(
        timestamp=scan.timestamp,
        start_hz=scan.start_hz,
        stop_hz=scan.stop_hz,
        bin_hz=scan.bin_hz,
        bins=tuple(adjusted),
        antenna_tag=scan.antenna_tag,
        location_tag=scan.location_tag,
    )


def _validate_compatible(scan: ScanResult, baseline_meta: ScanMeta) -> None:
    if scan.start_hz != baseline_meta.start_hz:
        raise ValueError("baseline start_hz mismatch")
    if scan.stop_hz != baseline_meta.stop_hz:
        raise ValueError("baseline stop_hz mismatch")
    if scan.bin_hz != baseline_meta.bin_hz:
        raise ValueError("baseline bin_hz mismatch")
