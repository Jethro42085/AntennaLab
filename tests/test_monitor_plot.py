from pathlib import Path
import json

from antennalab.report.monitor_plot import plot_monitor_summary


def test_monitor_plot(tmp_path: Path) -> None:
    summary = {
        "records": [
            {
                "timestamp": "2024-01-01T00:00:00+00:00",
                "scan_csv": str(tmp_path / "scan_0.csv"),
                "report_json": str(tmp_path / "report_0.json"),
            },
            {
                "timestamp": "2024-01-01T00:01:00+00:00",
                "scan_csv": str(tmp_path / "scan_1.csv"),
                "report_json": str(tmp_path / "report_1.json"),
            },
        ]
    }
    (tmp_path / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
    (tmp_path / "report_0.json").write_text(
        json.dumps({"timestamp": "2024-01-01T00:00:00+00:00", "avg_db_range": {"max": -50}, "max_db_range": {"max": -40}}),
        encoding="utf-8",
    )
    (tmp_path / "report_1.json").write_text(
        json.dumps({"timestamp": "2024-01-01T00:01:00+00:00", "avg_db_range": {"max": -48}, "max_db_range": {"max": -38}}),
        encoding="utf-8",
    )

    out_png = tmp_path / "monitor.png"
    plot_monitor_summary(tmp_path / "summary.json", out_png)

    assert out_png.exists()
    assert out_png.stat().st_size > 0
