from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from antennalab.report.export_csv import read_scan_csv


@dataclass(frozen=True)
class AlertRule:
    freq_hz: float
    threshold_db: float


@dataclass(frozen=True)
class AlertHit:
    timestamp: str
    freq_hz: float
    power_db: float
    threshold_db: float


class AlertEngine:
    def __init__(self, rules: Iterable[AlertRule]) -> None:
        self.rules = list(rules)

    def evaluate(self, scan_csv: str | Path) -> list[AlertHit]:
        _, bins = read_scan_csv(scan_csv)
        hits: list[AlertHit] = []
        now = datetime.now(timezone.utc).isoformat()
        for rule in self.rules:
            for bin_ in bins:
                if bin_.freq_hz == rule.freq_hz and bin_.max_db >= rule.threshold_db:
                    hits.append(
                        AlertHit(
                            timestamp=now,
                            freq_hz=bin_.freq_hz,
                            power_db=bin_.max_db,
                            threshold_db=rule.threshold_db,
                        )
                    )
        return hits


def load_alert_rules(path: str | Path) -> list[AlertRule]:
    input_path = Path(path)
    if not input_path.exists():
        raise FileNotFoundError(f"alerts config not found: {path}")
    rules: list[AlertRule] = []
    for line in input_path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        parts = [p.strip() for p in line.split(",")]
        if len(parts) != 2:
            raise ValueError(f"invalid alert rule: {line}")
        rules.append(AlertRule(freq_hz=float(parts[0]), threshold_db=float(parts[1])))
    return rules


def write_alert_hits(hits: list[AlertHit], path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines = ["timestamp,freq_hz,power_db,threshold_db"]
    for hit in hits:
        lines.append(
            f"{hit.timestamp},{hit.freq_hz:.0f},{hit.power_db:.2f},{hit.threshold_db:.2f}"
        )

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path
