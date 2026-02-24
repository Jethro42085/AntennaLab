from pathlib import Path

from antennalab.analysis.calibration_profiles import BaselineProfile, get_profile, upsert_profile


def test_upsert_and_get(tmp_path: Path) -> None:
    path = tmp_path / "profiles.json"
    profile = BaselineProfile(tag="night", csv_path="baseline.csv", created_at="t")
    upsert_profile(path, profile)

    loaded = get_profile(path, "night")
    assert loaded is not None
    assert loaded.csv_path == "baseline.csv"
