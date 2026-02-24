from __future__ import annotations

import math
import random

from antennalab.core.models import ScanBin, ScanResult


class ScanSimulator:
    def __init__(self, seed: int | None = None) -> None:
        self._rng = random.Random(seed)

    def simulate_scan(
        self,
        start_hz: float,
        stop_hz: float,
        bin_hz: float,
        antenna_tag: str | None = None,
        location_tag: str | None = None,
    ) -> ScanResult:
        if bin_hz <= 0:
            raise ValueError("bin_hz must be positive")
        if stop_hz <= start_hz:
            raise ValueError("stop_hz must be greater than start_hz")

        bins: list[ScanBin] = []
        freq = float(start_hz)
        center = (start_hz + stop_hz) / 2.0
        span = max(stop_hz - start_hz, 1.0)

        while freq < stop_hz:
            noise = -55 + self._rng.uniform(-6, 6)
            ripple = 6 * math.sin((freq - center) / span * 6.0 * math.pi)
            peak = 0.0
            if self._rng.random() < 0.02:
                peak = self._rng.uniform(8, 18)
            avg_db = noise + ripple
            max_db = avg_db + peak + self._rng.uniform(0, 4)
            bins.append(ScanBin(freq_hz=freq, avg_db=avg_db, max_db=max_db))
            freq += bin_hz

        return ScanResult(
            timestamp=ScanResult.now_iso(),
            start_hz=start_hz,
            stop_hz=stop_hz,
            bin_hz=bin_hz,
            bins=tuple(bins),
            antenna_tag=antenna_tag,
            location_tag=location_tag,
        )
