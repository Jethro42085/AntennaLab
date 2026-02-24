from pathlib import Path

from antennalab.analysis.compare import compare_scans
from antennalab.core.models import ScanBin, ScanResult
from antennalab.report.export_csv import write_scan_csv


def test_compare_scans_score(tmp_path: Path) -> None:
    scan_a = ScanResult(
        timestamp="2024-01-01T00:00:00+00:00",
        start_hz=100.0,
        stop_hz=120.0,
        bin_hz=10.0,
        bins=(
            ScanBin(freq_hz=100.0, avg_db=-50.0, max_db=-40.0),
            ScanBin(freq_hz=110.0, avg_db=-55.0, max_db=-42.0),
        ),
    )
    scan_b = ScanResult(
        timestamp="2024-01-01T00:01:00+00:00",
        start_hz=100.0,
        stop_hz=120.0,
        bin_hz=10.0,
        bins=(
            ScanBin(freq_hz=100.0, avg_db=-48.0, max_db=-39.0),
            ScanBin(freq_hz=110.0, avg_db=-52.0, max_db=-41.0),
        ),
    )

    path_a = tmp_path / "scan_a.csv"
    path_b = tmp_path / "scan_b.csv"
    write_scan_csv(scan_a, path_a)
    write_scan_csv(scan_b, path_b)

    result = compare_scans(path_a, path_b)
    assert len(result.bins) == 2
    assert round(result.score, 3) == 2.5
