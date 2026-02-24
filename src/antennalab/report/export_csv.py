from __future__ import annotations

import csv
from pathlib import Path

from antennalab.core.models import ScanResult


def write_scan_csv(scan: ScanResult, path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow([
            "timestamp",
            "start_hz",
            "stop_hz",
            "bin_hz",
            "antenna_tag",
            "location_tag",
        ])
        writer.writerow([
            scan.timestamp,
            scan.start_hz,
            scan.stop_hz,
            scan.bin_hz,
            scan.antenna_tag or "",
            scan.location_tag or "",
        ])
        writer.writerow(["freq_hz", "avg_db", "max_db"])
        for scan_bin in scan.iter_bins():
            writer.writerow([
                f"{scan_bin.freq_hz:.0f}",
                f"{scan_bin.avg_db:.2f}",
                f"{scan_bin.max_db:.2f}",
            ])

    return output_path
