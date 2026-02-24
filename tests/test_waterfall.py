from pathlib import Path

from antennalab.analysis.waterfall import WaterfallSettings, run_waterfall


def test_waterfall_sim(tmp_path: Path) -> None:
    out_csv = tmp_path / "waterfall.csv"
    settings = WaterfallSettings(
        mode="sim",
        start_hz=100.0,
        stop_hz=110.0,
        bin_hz=5.0,
        slices=3,
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
    run_waterfall(settings, out_csv)
    content = out_csv.read_text(encoding="utf-8").splitlines()
    assert content[0].startswith("timestamp,slice_index")
    # 2 bins per slice (100,105) * 3 slices + header
    assert len(content) == 1 + 2 * 3
