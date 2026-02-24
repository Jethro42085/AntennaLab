from pathlib import Path

from antennalab.bookmarks import Bookmark, add_bookmark, load_bookmarks, remove_bookmark


def test_add_and_list_bookmarks(tmp_path: Path) -> None:
    path = tmp_path / "bookmarks.csv"
    add_bookmark(path, Bookmark(freq_hz=100.0, label="Test", notes="note"))
    add_bookmark(path, Bookmark(freq_hz=90.0, label="Low", notes=""))

    bookmarks = load_bookmarks(path)
    assert len(bookmarks) == 2
    assert bookmarks[0].freq_hz == 90.0
    assert bookmarks[1].freq_hz == 100.0


def test_remove_by_freq(tmp_path: Path) -> None:
    path = tmp_path / "bookmarks.csv"
    add_bookmark(path, Bookmark(freq_hz=100.0, label="A", notes=""))
    add_bookmark(path, Bookmark(freq_hz=110.0, label="B", notes=""))

    _, removed = remove_bookmark(path, freq_hz=100.0, label=None)
    assert removed == 1
    bookmarks = load_bookmarks(path)
    assert len(bookmarks) == 1
    assert bookmarks[0].freq_hz == 110.0
