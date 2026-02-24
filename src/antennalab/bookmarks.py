from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path

from antennalab.report.export_csv import read_scan_csv


@dataclass(frozen=True)
class Bookmark:
    freq_hz: float
    label: str
    notes: str


def load_bookmarks(path: str | Path) -> list[Bookmark]:
    input_path = Path(path)
    if not input_path.exists():
        return []
    bookmarks: list[Bookmark] = []
    with input_path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        header = next(reader, None)
        if header and header[:3] != ["freq_hz", "label", "notes"]:
            raise ValueError("unexpected bookmarks CSV header")
        for row in reader:
            if not row:
                continue
            freq_hz = float(row[0])
            label = row[1] if len(row) > 1 else ""
            notes = row[2] if len(row) > 2 else ""
            bookmarks.append(Bookmark(freq_hz=freq_hz, label=label, notes=notes))
    return bookmarks


def save_bookmarks(path: str | Path, bookmarks: list[Bookmark]) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["freq_hz", "label", "notes"])
        for bm in bookmarks:
            writer.writerow([f"{bm.freq_hz:.0f}", bm.label, bm.notes])
    return output_path


def add_bookmark(path: str | Path, bookmark: Bookmark) -> Path:
    bookmarks = load_bookmarks(path)
    bookmarks.append(bookmark)
    bookmarks.sort(key=lambda b: b.freq_hz)
    return save_bookmarks(path, bookmarks)


def remove_bookmark(path: str | Path, freq_hz: float | None, label: str | None) -> tuple[Path, int]:
    bookmarks = load_bookmarks(path)
    before = len(bookmarks)
    remaining = []
    for bm in bookmarks:
        if freq_hz is not None and bm.freq_hz == freq_hz:
            continue
        if label is not None and bm.label == label:
            continue
        remaining.append(bm)
    removed = before - len(remaining)
    return save_bookmarks(path, remaining), removed


def export_bookmarks_json(path: str | Path, out_json: str | Path) -> Path:
    bookmarks = load_bookmarks(path)
    payload = [
        {"freq_hz": bm.freq_hz, "label": bm.label, "notes": bm.notes}
        for bm in bookmarks
    ]
    output_path = Path(out_json)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return output_path


def import_bookmarks_json(path: str | Path, in_json: str | Path) -> Path:
    input_path = Path(in_json)
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    bookmarks = [
        Bookmark(freq_hz=float(item["freq_hz"]), label=item.get("label", ""), notes=item.get("notes", ""))
        for item in payload
    ]
    bookmarks.sort(key=lambda b: b.freq_hz)
    return save_bookmarks(path, bookmarks)


def match_bookmarks_to_scan(scan_csv: str | Path, bookmarks_file: str | Path) -> list[Bookmark]:
    meta, _ = read_scan_csv(scan_csv)
    bookmarks = load_bookmarks(bookmarks_file)
    return [
        bm
        for bm in bookmarks
        if meta.start_hz <= bm.freq_hz <= meta.stop_hz
    ]
