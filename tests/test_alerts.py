from pathlib import Path

from antennalab.analysis.alerts import AlertEngine, AlertRule, load_alert_rules
from antennalab.core.models import ScanBin, ScanResult
from antennalab.report.export_csv import write_scan_csv


def test_alert_engine_hits(tmp_path: Path) -> None:
    scan = ScanResult(
        timestamp="2024-01-01T00:00:00+00:00",
        start_hz=100.0,
        stop_hz=120.0,
        bin_hz=10.0,
        bins=(
            ScanBin(freq_hz=100.0, avg_db=-50.0, max_db=-25.0),
            ScanBin(freq_hz=110.0, avg_db=-60.0, max_db=-55.0),
        ),
    )
    scan_path = tmp_path / "scan.csv"
    write_scan_csv(scan, scan_path)

    engine = AlertEngine([AlertRule(freq_hz=100.0, threshold_db=-30.0)])
    hits = engine.evaluate(scan_path)
    assert len(hits) == 1
    assert hits[0].freq_hz == 100.0


def test_load_alert_rules(tmp_path: Path) -> None:
    rules_path = tmp_path / "alerts.csv"
    rules_path.write_text("100,-30\n", encoding="utf-8")
    rules = load_alert_rules(rules_path)
    assert len(rules) == 1
    assert rules[0].freq_hz == 100.0
    assert rules[0].threshold_db == -30.0
