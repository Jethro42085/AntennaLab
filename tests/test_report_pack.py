from pathlib import Path
import json

from antennalab.report.report_pack import build_report_pack


def test_report_pack(tmp_path: Path) -> None:
    scans = tmp_path / "scans"
    reports = tmp_path / "reports"
    waterfalls = tmp_path / "waterfalls"
    out = tmp_path / "out"

    scans.mkdir()
    reports.mkdir()
    waterfalls.mkdir()

    (scans / "scan.csv").write_text("scan", encoding="utf-8")
    (reports / "scan_report.json").write_text(
        json.dumps({"timestamp": "t", "start_hz": 1, "stop_hz": 2, "bin_hz": 3}),
        encoding="utf-8",
    )
    (waterfalls / "waterfall.csv").write_text("water", encoding="utf-8")

    pack_dir, copied = build_report_pack(
        session_name="test",
        scans_dir=scans,
        reports_dir=reports,
        waterfalls_dir=waterfalls,
        out_dir=out,
    )

    assert copied >= 3
    assert (pack_dir / "scan.csv").exists()
    assert (pack_dir / "scan_report.json").exists()
    assert (pack_dir / "waterfall.csv").exists()
    assert (pack_dir / "summary.json").exists()
