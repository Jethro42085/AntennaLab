from pathlib import Path

from antennalab.analysis.waterfall import WaterfallSettings, run_waterfall
from antennalab.report.waterfall_html import write_waterfall_html


def test_waterfall_html(tmp_path: Path) -> None:
    waterfall_csv = tmp_path / "waterfall.csv"
    settings = WaterfallSettings(
        mode="sim",
        start_hz=100.0,
        stop_hz=110.0,
        bin_hz=5.0,
        slices=2,
        interval_ms=0,
        sample_rate_hz=2_400_000,
        gain_db="auto",
        fft_size=1024,
        step_hz=None,
        sweeps=1,
        dwell_ms=0,
        missing_db=-120.0,
        seed=1,
    )
    run_waterfall(settings, waterfall_csv)

    out_html = tmp_path / "waterfall.html"
    write_waterfall_html(waterfall_csv, out_html)

    content = out_html.read_text(encoding="utf-8")
    assert "AntennaLab Waterfall" in content
    assert "canvas" in content
