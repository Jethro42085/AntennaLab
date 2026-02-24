from pathlib import Path

from antennalab.analysis.monitor import MonitorSettings, run_monitor


def test_monitor_sim(tmp_path: Path) -> None:
    out_dir = tmp_path / "monitor"
    settings = MonitorSettings(
        mode="sim",
        start_hz=100.0,
        stop_hz=110.0,
        bin_hz=5.0,
        sample_rate_hz=2_400_000,
        gain_db="auto",
        fft_size=1024,
        step_hz=None,
        sweeps=1,
        dwell_ms=0,
        missing_db=-120.0,
        interval_sec=1,
        iterations=2,
        seed=1,
        bookmarks_file=None,
    )
    summary_path = run_monitor(settings, out_dir=out_dir)
    assert summary_path.exists()
    scans = list((out_dir / "scans").glob("scan_*.csv"))
    reports = list((out_dir / "reports").glob("report_*.json"))
    assert len(scans) == 2
    assert len(reports) == 2
