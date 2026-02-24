from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from antennalab.core.models import ScanResult


def write_run_report(scan: ScanResult, path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    payload: dict[str, Any] = {
        "timestamp": scan.timestamp,
        "start_hz": scan.start_hz,
        "stop_hz": scan.stop_hz,
        "bin_hz": scan.bin_hz,
        "antenna_tag": scan.antenna_tag,
        "location_tag": scan.location_tag,
        "bins": len(scan.bins),
        "avg_db_range": {
            "min": min(b.avg_db for b in scan.bins) if scan.bins else None,
            "max": max(b.avg_db for b in scan.bins) if scan.bins else None,
        },
        "max_db_range": {
            "min": min(b.max_db for b in scan.bins) if scan.bins else None,
            "max": max(b.max_db for b in scan.bins) if scan.bins else None,
        },
    }

    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")

    return output_path
