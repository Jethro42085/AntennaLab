from pathlib import Path

from antennalab.analysis.calibration_profiles import (
    BaselineProfile,
    get_profile,
    remove_profile,
    upsert_profile,
)


def test_upsert_and_get(tmp_path: Path) -> None:
    path = tmp_path / "profiles.json"
    profile = BaselineProfile(tag="night", csv_path="baseline.csv", created_at="t")
    upsert_profile(path, profile)

    loaded = get_profile(path, "night")
    assert loaded is not None
    assert loaded.csv_path == "baseline.csv"


def test_remove_profile(tmp_path: Path) -> None:
    path = tmp_path / "profiles.json"
    profile = BaselineProfile(tag="night", csv_path="baseline.csv", created_at="t")
    upsert_profile(path, profile)

    removed = remove_profile(path, "night")
    assert removed is True
    assert get_profile(path, "night") is None
