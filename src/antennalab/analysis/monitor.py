from __future__ import annotations

import json
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from antennalab.bookmarks import load_bookmarks, match_bookmarks_to_range
from antennalab.core.models import ScanResult
from antennalab.instruments.rtlsdr import RTLSDRPlugin
from antennalab.report.export_csv import write_scan_csv
from antennalab.report.run_report import write_run_report


@dataclass(frozen=True)
class MonitorSettings:
    mode: str
    start_hz: float
    stop_hz: float
    bin_hz: float
    sample_rate_hz: float
    gain_db: float | str
    fft_size: int
    step_hz: float | None
    sweeps: int
    dwell_ms: int
    missing_db: float
    interval_sec: int
    iterations: int
    seed: int | None
    bookmarks_file: Path | None


def _timestamp_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def _bookmark_payload(bookmarks_file: Path | None, scan: ScanResult) -> list[dict] | None:
    if not bookmarks_file:
        return None
    bookmarks = load_bookmarks(bookmarks_file)
    if not bookmarks:
        return []
    matched = match_bookmarks_to_range(bookmarks, scan.start_hz, scan.stop_hz)
    return [
        {"freq_hz": bm.freq_hz, "label": bm.label, "notes": bm.notes}
        for bm in matched
    ]


def run_monitor(
    settings: MonitorSettings,
    *,
    out_dir: Path,
) -> Path:
    if settings.interval_sec <= 0:
        raise ValueError("interval_sec must be > 0")
    if settings.iterations <= 0:
        raise ValueError("iterations must be > 0")

    out_dir.mkdir(parents=True, exist_ok=True)
    scans_dir = out_dir / "scans"
    reports_dir = out_dir / "reports"
    scans_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    plugin = RTLSDRPlugin()
    records: list[dict] = []

    for idx in range(settings.iterations):
        seed = settings.seed + idx if settings.seed is not None else None
        if settings.mode == "sim":
            scan = plugin.scan_simulated(
                start_hz=settings.start_hz,
                stop_hz=settings.stop_hz,
                bin_hz=settings.bin_hz,
                antenna_tag=None,
                location_tag=None,
                seed=seed,
            )
        else:
            scan = plugin.scan_real(
                start_hz=settings.start_hz,
                stop_hz=settings.stop_hz,
                bin_hz=settings.bin_hz,
                sample_rate_hz=settings.sample_rate_hz,
                gain_db=settings.gain_db,
                fft_size=settings.fft_size,
                step_hz=settings.step_hz,
                sweeps=settings.sweeps,
                dwell_ms=settings.dwell_ms,
                missing_db=settings.missing_db,
                antenna_tag=None,
                location_tag=None,
            )

        stamp = _timestamp_slug()
        scan_path = scans_dir / f"scan_{stamp}.csv"
        report_path = reports_dir / f"report_{stamp}.json"

        write_scan_csv(scan, scan_path)
        bookmarks_payload = _bookmark_payload(settings.bookmarks_file, scan)
        write_run_report(scan, report_path, bookmarks=bookmarks_payload)

        records.append({
            "timestamp": scan.timestamp,
            "scan_csv": str(scan_path),
            "report_json": str(report_path),
        })

        if idx < settings.iterations - 1:
            time.sleep(settings.interval_sec)

    summary = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "iterations": settings.iterations,
        "interval_sec": settings.interval_sec,
        "mode": settings.mode,
        "start_hz": settings.start_hz,
        "stop_hz": settings.stop_hz,
        "bin_hz": settings.bin_hz,
        "records": records,
    }
    summary_path = out_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary_path
