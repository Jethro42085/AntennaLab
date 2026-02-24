from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from antennalab.core.models import ScanBin, ScanResult, SweepStatsBin


@dataclass(frozen=True)
class ScanMeta:
    timestamp: str
    start_hz: float
    stop_hz: float
    bin_hz: float
    antenna_tag: str | None
    location_tag: str | None


def write_scan_csv(scan: ScanResult, path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "timestamp",
                "start_hz",
                "stop_hz",
                "bin_hz",
                "antenna_tag",
                "location_tag",
            ]
        )
        writer.writerow(
            [
                scan.timestamp,
                scan.start_hz,
                scan.stop_hz,
                scan.bin_hz,
                scan.antenna_tag or "",
                scan.location_tag or "",
            ]
        )
        writer.writerow(["freq_hz", "avg_db", "max_db"])
        for scan_bin in scan.iter_bins():
            writer.writerow(
                [
                    f"{scan_bin.freq_hz:.0f}",
                    f"{scan_bin.avg_db:.2f}",
                    f"{scan_bin.max_db:.2f}",
                ]
            )

    return output_path


def read_scan_csv(path: str | Path) -> tuple[ScanMeta, list[ScanBin]]:
    input_path = Path(path)
    with input_path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        header = next(reader)
        values = next(reader)
        if header[:4] != ["timestamp", "start_hz", "stop_hz", "bin_hz"]:
            raise ValueError("unexpected scan CSV header")
        meta = ScanMeta(
            timestamp=values[0],
            start_hz=float(values[1]),
            stop_hz=float(values[2]),
            bin_hz=float(values[3]),
            antenna_tag=values[4] or None,
            location_tag=values[5] or None,
        )
        bins_header = next(reader)
        if bins_header[:3] != ["freq_hz", "avg_db", "max_db"]:
            raise ValueError("unexpected scan CSV bins header")
        bins: list[ScanBin] = []
        for row in reader:
            if not row:
                continue
            bins.append(
                ScanBin(
                    freq_hz=float(row[0]),
                    avg_db=float(row[1]),
                    max_db=float(row[2]),
                )
            )
    return meta, bins


def scan_from_csv(path: str | Path) -> ScanResult:
    meta, bins = read_scan_csv(path)
    return ScanResult(
        timestamp=meta.timestamp,
        start_hz=meta.start_hz,
        stop_hz=meta.stop_hz,
        bin_hz=meta.bin_hz,
        bins=tuple(bins),
        antenna_tag=meta.antenna_tag,
        location_tag=meta.location_tag,
    )


def write_noise_floor_csv(
    result: "NoiseFloorResult",
    path: str | Path,
    *,
    scan_meta: ScanMeta,
    strategy: str,
) -> Path:
    from antennalab.analysis.noise_floor import NoiseFloorResult

    if not isinstance(result, NoiseFloorResult):
        raise TypeError("result must be NoiseFloorResult")

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "timestamp",
                "start_hz",
                "stop_hz",
                "bin_hz",
                "antenna_tag",
                "location_tag",
                "strategy",
            ]
        )
        writer.writerow(
            [
                scan_meta.timestamp,
                scan_meta.start_hz,
                scan_meta.stop_hz,
                scan_meta.bin_hz,
                scan_meta.antenna_tag or "",
                scan_meta.location_tag or "",
                strategy,
            ]
        )
        writer.writerow(["freq_hz", "noise_floor_db"])
        for bin_ in result.bins:
            writer.writerow(
                [
                    f"{bin_.freq_hz:.0f}",
                    f"{bin_.noise_floor_db:.2f}",
                ]
            )

    return output_path


def write_compare_csv(result: "CompareResult", path: str | Path) -> Path:
    from antennalab.analysis.compare import CompareResult

    if not isinstance(result, CompareResult):
        raise TypeError("result must be CompareResult")

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["scan_a", "scan_b", "score"])
        writer.writerow([result.scan_a, result.scan_b, f"{result.score:.3f}"])
        writer.writerow(["freq_hz", "delta_avg_db", "delta_max_db"])
        for bin_ in result.bins:
            writer.writerow(
                [
                    f"{bin_.freq_hz:.0f}",
                    f"{bin_.delta_avg_db:.2f}",
                    f"{bin_.delta_max_db:.2f}",
                ]
            )

    return output_path


def write_sweep_stats_csv(
    bins: Iterable[SweepStatsBin],
    path: str | Path,
) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["freq_hz", "sweep_avg_min_db", "sweep_avg_mean_db", "sweep_avg_max_db"])
        for bin_ in bins:
            writer.writerow(
                [
                    f"{bin_.freq_hz:.0f}",
                    f"{bin_.sweep_avg_min_db:.2f}",
                    f"{bin_.sweep_avg_mean_db:.2f}",
                    f"{bin_.sweep_avg_max_db:.2f}",
                ]
            )

    return output_path
