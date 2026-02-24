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

    # Common outputs
    copy_if_exists(scans_dir / "scan.csv", pack_dir / "scan.csv")
    copy_if_exists(scans_dir / "baseline.csv", pack_dir / "baseline.csv")
    copy_if_exists(scans_dir / "scan_adjusted.csv", pack_dir / "scan_adjusted.csv")
    copy_if_exists(reports_dir / "scan_report.json", pack_dir / "scan_report.json")
    copy_if_exists(reports_dir / "noise_floor.csv", pack_dir / "noise_floor.csv")
    copy_if_exists(reports_dir / "compare.csv", pack_dir / "compare.csv")
    copy_if_exists(reports_dir / "sweep_stats.csv", pack_dir / "sweep_stats.csv")
    copy_if_exists(reports_dir / "alerts.csv", pack_dir / "alerts.csv")
    copy_if_exists(reports_dir / "scan.png", pack_dir / "scan.png")
    copy_if_exists(reports_dir / "waterfall.png", pack_dir / "waterfall.png")
    copy_if_exists(reports_dir / "waterfall.html", pack_dir / "waterfall.html")
    copy_if_exists(reports_dir / "bookmarks.json", pack_dir / "bookmarks.json")
    copy_if_exists(waterfalls_dir / "waterfall.csv", pack_dir / "waterfall.csv")

    return pack_dir
