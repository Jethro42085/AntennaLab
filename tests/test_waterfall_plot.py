from pathlib import Path

from antennalab.analysis.waterfall import WaterfallSettings, run_waterfall
from antennalab.report.waterfall_plot import plot_waterfall_csv


def test_plot_waterfall(tmp_path: Path) -> None:
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

    out_png = tmp_path / "waterfall.png"
    plot_waterfall_csv(waterfall_csv, out_png)

    assert out_png.exists()
    assert out_png.stat().st_size > 0
