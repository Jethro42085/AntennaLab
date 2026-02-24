from __future__ import annotations

import csv
import time
from dataclasses import dataclass
from pathlib import Path

from antennalab.analysis.spectrum import ScanSimulator
from antennalab.core.models import ScanResult
from antennalab.instruments.rtlsdr import RTLSDRPlugin


@dataclass(frozen=True)
class WaterfallSettings:
    mode: str
    start_hz: float
    stop_hz: float
    bin_hz: float
    slices: int
    interval_ms: int
    sample_rate_hz: float
    gain_db: float | str
    fft_size: int
    step_hz: float | None
    sweeps: int
    dwell_ms: int
    missing_db: float
    seed: int | None


def write_waterfall_csv(path: str | Path, slices: list[tuple[str, int, ScanResult]]) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["timestamp", "slice_index", "freq_hz", "avg_db", "max_db"])
        for timestamp, slice_index, scan in slices:
            for bin_ in scan.bins:
                writer.writerow(
                    [
                        timestamp,
                        slice_index,
                        f"{bin_.freq_hz:.0f}",
                        f"{bin_.avg_db:.2f}",
                        f"{bin_.max_db:.2f}",
                    ]
                )

    return output_path


def run_waterfall(settings: WaterfallSettings, out_csv: str | Path) -> Path:
    if settings.slices <= 0:
        raise ValueError("slices must be positive")
    if settings.interval_ms < 0:
        raise ValueError("interval_ms must be >= 0")

    plugin = RTLSDRPlugin()
    simulator = ScanSimulator(seed=settings.seed) if settings.mode == "sim" else None

    slices: list[tuple[str, int, ScanResult]] = []
    for idx in range(settings.slices):
        if settings.mode == "sim":
            seed = None
            if settings.seed is not None:
                seed = settings.seed + idx
            scan = ScanSimulator(seed=seed).simulate_scan(
                start_hz=settings.start_hz,
                stop_hz=settings.stop_hz,
                bin_hz=settings.bin_hz,
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
        slices.append((scan.timestamp, idx, scan))
        if settings.interval_ms:
            time.sleep(settings.interval_ms / 1000.0)

    return write_waterfall_csv(out_csv, slices)
