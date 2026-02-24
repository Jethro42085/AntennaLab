from pathlib import Path

from antennalab.analysis.noise_floor import estimate_noise_floor
from antennalab.core.models import ScanBin, ScanResult
from antennalab.report.export_csv import read_scan_csv, write_scan_csv


def test_noise_floor_avg(tmp_path: Path) -> None:
    scan = ScanResult(
        timestamp="2024-01-01T00:00:00+00:00",
        start_hz=100.0,
        stop_hz=120.0,
        bin_hz=10.0,
        bins=(
            ScanBin(freq_hz=100.0, avg_db=-50.0, max_db=-40.0),
            ScanBin(freq_hz=110.0, avg_db=-55.0, max_db=-45.0),
        ),
    )
    scan_path = tmp_path / "scan.csv"
    write_scan_csv(scan, scan_path)

    out_path = tmp_path / "noise.csv"
    estimate_noise_floor(scan_path, out_path)

    meta, bins = read_scan_csv(scan_path)
    assert meta.start_hz == 100.0
    assert len(bins) == 2

    content = out_path.read_text(encoding="utf-8")
    assert "noise_floor_db" in content
    assert "-50.00" in content
    assert "-55.00" in content
