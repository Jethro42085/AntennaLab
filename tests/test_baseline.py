from pathlib import Path

from antennalab.analysis.calibration import apply_baseline, load_baseline
from antennalab.core.models import ScanBin, ScanResult
from antennalab.report.export_csv import write_scan_csv


def test_apply_baseline(tmp_path: Path) -> None:
    baseline = ScanResult(
        timestamp="2024-01-01T00:00:00+00:00",
        start_hz=100.0,
        stop_hz=120.0,
        bin_hz=10.0,
        bins=(
            ScanBin(freq_hz=100.0, avg_db=-60.0, max_db=-55.0),
            ScanBin(freq_hz=110.0, avg_db=-62.0, max_db=-56.0),
        ),
    )
    baseline_path = tmp_path / "baseline.csv"
    write_scan_csv(baseline, baseline_path)

    scan = ScanResult(
        timestamp="2024-01-01T00:01:00+00:00",
        start_hz=100.0,
        stop_hz=120.0,
        bin_hz=10.0,
        bins=(
            ScanBin(freq_hz=100.0, avg_db=-50.0, max_db=-40.0),
            ScanBin(freq_hz=110.0, avg_db=-52.0, max_db=-41.0),
        ),
    )

    baseline_loaded = load_baseline(baseline_path)
    adjusted = apply_baseline(scan, baseline_loaded)

    assert adjusted.bins[0].avg_db == 10.0
    assert adjusted.bins[0].max_db == 20.0
    assert adjusted.bins[1].avg_db == 10.0
    assert adjusted.bins[1].max_db == 21.0
