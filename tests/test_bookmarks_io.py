from pathlib import Path

from antennalab.bookmarks import (
    Bookmark,
    add_bookmark,
    export_bookmarks_json,
    import_bookmarks_json,
    load_bookmarks,
    match_bookmarks_to_scan,
)
from antennalab.core.models import ScanBin, ScanResult
from antennalab.report.export_csv import write_scan_csv


def test_export_import_json(tmp_path: Path) -> None:
    bookmarks_csv = tmp_path / "bookmarks.csv"
    add_bookmark(bookmarks_csv, Bookmark(freq_hz=100.0, label="A", notes=""))
    out_json = tmp_path / "bookmarks.json"

    export_bookmarks_json(bookmarks_csv, out_json)
    assert out_json.exists()

    new_csv = tmp_path / "imported.csv"
    import_bookmarks_json(new_csv, out_json)
    bookmarks = load_bookmarks(new_csv)
    assert len(bookmarks) == 1
    assert bookmarks[0].freq_hz == 100.0


def test_match_bookmarks_to_scan(tmp_path: Path) -> None:
    scan = ScanResult(
        timestamp="2024-01-01T00:00:00+00:00",
        start_hz=90.0,
        stop_hz=110.0,
        bin_hz=10.0,
        bins=(
            ScanBin(freq_hz=90.0, avg_db=-50.0, max_db=-40.0),
            ScanBin(freq_hz=100.0, avg_db=-50.0, max_db=-40.0),
            ScanBin(freq_hz=110.0, avg_db=-50.0, max_db=-40.0),
        ),
    )
    scan_path = tmp_path / "scan.csv"
    write_scan_csv(scan, scan_path)

    bookmarks_csv = tmp_path / "bookmarks.csv"
    add_bookmark(bookmarks_csv, Bookmark(freq_hz=95.0, label="Mid", notes=""))
    add_bookmark(bookmarks_csv, Bookmark(freq_hz=120.0, label="Out", notes=""))

    matches = match_bookmarks_to_scan(scan_path, bookmarks_csv)
    assert len(matches) == 1
    assert matches[0].freq_hz == 95.0
