from __future__ import annotations

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


def build_report_pack(
    *,
    session_name: str | None,
    scans_dir: Path,
    reports_dir: Path,
    waterfalls_dir: Path,
    out_dir: Path,
) -> Path:
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

    return pack_dir, copied
