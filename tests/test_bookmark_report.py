from pathlib import Path

from antennalab.bookmarks import Bookmark, add_bookmark, match_bookmarks_to_range
from antennalab.core.models import ScanResult, ScanBin
from antennalab.report.run_report import write_run_report


def test_run_report_includes_bookmarks(tmp_path: Path) -> None:
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
    bookmarks_csv = tmp_path / "bookmarks.csv"
    add_bookmark(bookmarks_csv, Bookmark(freq_hz=95.0, label="Mid", notes=""))
    add_bookmark(bookmarks_csv, Bookmark(freq_hz=120.0, label="Out", notes=""))

    matched = match_bookmarks_to_range(
        [Bookmark(freq_hz=95.0, label="Mid", notes="")], 90.0, 110.0
    )
    payload = [
        {"freq_hz": bm.freq_hz, "label": bm.label, "notes": bm.notes}
        for bm in matched
    ]

    out_json = tmp_path / "report.json"
    write_run_report(scan, out_json, bookmarks=payload)

    content = out_json.read_text(encoding="utf-8")
    assert "bookmarks" in content
    assert "95.0" in content
