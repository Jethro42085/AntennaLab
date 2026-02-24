from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


def plot_monitor_summary(input_json: str | Path, output_png: str | Path) -> Path:
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:  # pragma: no cover
        raise SystemExit("monitor-plot requires matplotlib. Install with: pip install matplotlib") from exc

    input_path = Path(input_json)
    summary = json.loads(input_path.read_text(encoding="utf-8"))
    records = summary.get("records", [])
    if not records:
        raise ValueError("monitor summary has no records")

    times: list[datetime] = []
    avg_max: list[float] = []
    max_max: list[float] = []

    for record in records:
        report_path = Path(record["report_json"])
        report = json.loads(report_path.read_text(encoding="utf-8"))
        ts = report.get("timestamp")
        if ts is None:
            continue
        times.append(datetime.fromisoformat(ts))
        avg_max.append(report.get("avg_db_range", {}).get("max", 0.0))
        max_max.append(report.get("max_db_range", {}).get("max", 0.0))

    output_path = Path(output_png)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(10, 4))
    plt.plot(times, avg_max, label="avg_db max")
    plt.plot(times, max_max, label="max_db max")
    plt.xlabel("Time")
    plt.ylabel("dB (relative)")
    plt.title("Monitor Summary")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=140)
    plt.close()

    return output_path
