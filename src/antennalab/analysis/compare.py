from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from antennalab.core.models import ScanBin
from antennalab.report.export_csv import ScanMeta, read_scan_csv, write_compare_csv


@dataclass(frozen=True)
class CompareBin:
    freq_hz: float
    delta_avg_db: float
    delta_max_db: float


@dataclass(frozen=True)
class CompareResult:
    scan_a: Path
    scan_b: Path
    bins: tuple[CompareBin, ...]
    score: float


def compare_scans(scan_a: str | Path, scan_b: str | Path) -> CompareResult:
    meta_a, bins_a = read_scan_csv(scan_a)
    meta_b, bins_b = read_scan_csv(scan_b)
    _validate_compatible(meta_a, meta_b)

    by_freq_b = {bin_.freq_hz: bin_ for bin_ in bins_b}
    compare_bins: list[CompareBin] = []
    score_accum = 0.0
    score_count = 0

    for bin_a in bins_a:
        bin_b = by_freq_b.get(bin_a.freq_hz)
        if bin_b is None:
            continue
        delta_avg = bin_b.avg_db - bin_a.avg_db
        delta_max = bin_b.max_db - bin_a.max_db
        compare_bins.append(
            CompareBin(
                freq_hz=bin_a.freq_hz,
                delta_avg_db=delta_avg,
                delta_max_db=delta_max,
            )
        )
        score_accum += delta_avg
        score_count += 1

    score = score_accum / score_count if score_count else 0.0
    return CompareResult(
        scan_a=Path(scan_a),
        scan_b=Path(scan_b),
        bins=tuple(compare_bins),
        score=score,
    )


def _validate_compatible(meta_a: ScanMeta, meta_b: ScanMeta) -> None:
    if meta_a.start_hz != meta_b.start_hz:
        raise ValueError("scan start_hz mismatch")
    if meta_a.stop_hz != meta_b.stop_hz:
        raise ValueError("scan stop_hz mismatch")
    if meta_a.bin_hz != meta_b.bin_hz:
        raise ValueError("scan bin_hz mismatch")


def compare_to_csv(scan_a: str | Path, scan_b: str | Path, out_csv: str | Path) -> Path:
    result = compare_scans(scan_a, scan_b)
    return write_compare_csv(result, out_csv)
