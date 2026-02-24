from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def copy_if_exists(src: Path, dst: Path) -> bool:
    if not src.exists():
        return False
    _ensure_dir(dst.parent)
    shutil.copy2(src, dst)
    return True


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _write_readme(path: Path, files: list[str], summary_path: Path) -> None:
    lines = [
        "AntennaLab Report Pack",
        "",
        "Files:",
    ]
    lines += [f"- {name}" for name in files]
    lines += [
        "",
        f"Summary: {summary_path.name}",
        "",
        "Tip: open waterfall.html in a browser if present.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_report_pack(
    *,
    session_name: str | None,
    scans_dir: Path,
    reports_dir: Path,
    waterfalls_dir: Path,
    out_dir: Path,
) -> tuple[Path, int]:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session = session_name or f"session_{timestamp}"

    pack_dir = out_dir / session
    _ensure_dir(pack_dir)
    copied = 0

    # Common outputs
    copied += int(copy_if_exists(scans_dir / "scan.csv", pack_dir / "scan.csv"))
    copied += int(copy_if_exists(scans_dir / "baseline.csv", pack_dir / "baseline.csv"))
    copied += int(copy_if_exists(scans_dir / "scan_adjusted.csv", pack_dir / "scan_adjusted.csv"))
    copied += int(copy_if_exists(reports_dir / "scan_report.json", pack_dir / "scan_report.json"))
    copied += int(copy_if_exists(reports_dir / "noise_floor.csv", pack_dir / "noise_floor.csv"))
    copied += int(copy_if_exists(reports_dir / "compare.csv", pack_dir / "compare.csv"))
    copied += int(copy_if_exists(reports_dir / "sweep_stats.csv", pack_dir / "sweep_stats.csv"))
    copied += int(copy_if_exists(reports_dir / "alerts.csv", pack_dir / "alerts.csv"))
    copied += int(copy_if_exists(reports_dir / "scan.png", pack_dir / "scan.png"))
    copied += int(copy_if_exists(reports_dir / "waterfall.png", pack_dir / "waterfall.png"))
    copied += int(copy_if_exists(reports_dir / "waterfall.html", pack_dir / "waterfall.html"))
    copied += int(copy_if_exists(reports_dir / "bookmarks.json", pack_dir / "bookmarks.json"))
    copied += int(copy_if_exists(waterfalls_dir / "waterfall.csv", pack_dir / "waterfall.csv"))

    files = sorted(p.name for p in pack_dir.iterdir() if p.is_file())

    summary = {
        "session": session,
        "created_at": timestamp,
        "files": files,
    }

    scan_report = _read_json(pack_dir / "scan_report.json")
    if scan_report:
        summary["scan_report"] = {
            "timestamp": scan_report.get("timestamp"),
            "start_hz": scan_report.get("start_hz"),
            "stop_hz": scan_report.get("stop_hz"),
            "bin_hz": scan_report.get("bin_hz"),
            "bookmarks": scan_report.get("bookmarks", []),
        }

    summary_path = pack_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    copied += 1

    _write_readme(pack_dir / "README.txt", files, summary_path)
    copied += 1

    return pack_dir, copied
