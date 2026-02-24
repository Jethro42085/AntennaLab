from __future__ import annotations

import math
import time

from antennalab.analysis.spectrum import ScanSimulator
from antennalab.core.models import ScanBin, ScanResult
from antennalab.core.plugins import HealthCheck, PluginInfo


class RTLSDRPlugin:
    def info(self) -> PluginInfo:
        return PluginInfo(
            name="rtl-sdr",
            kind="sdr",
            description="RTL-SDR relative spectrum scanner",
        )

    def healthcheck(self, config: dict) -> HealthCheck:
        device_cfg = config.get("device", {}) if isinstance(config, dict) else {}
        device_kind = device_cfg.get("kind", "rtlsdr")
        if device_kind not in ("rtlsdr", None):
            return HealthCheck(
                ok=False,
                status="error",
                detail="device.kind is not rtlsdr",
            )
        return HealthCheck(
            ok=True,
            status="ok",
            detail="Config looks valid; hardware check not implemented",
        )

    def scan_simulated(
        self,
        *,
        start_hz: float,
        stop_hz: float,
        bin_hz: float,
        antenna_tag: str | None,
        location_tag: str | None,
        seed: int | None,
    ) -> ScanResult:
        simulator = ScanSimulator(seed=seed)
        return simulator.simulate_scan(
            start_hz=start_hz,
            stop_hz=stop_hz,
            bin_hz=bin_hz,
            antenna_tag=antenna_tag,
            location_tag=location_tag,
        )

    def scan_real(
        self,
        *,
        start_hz: float,
        stop_hz: float,
        bin_hz: float,
        sample_rate_hz: float,
        gain_db: float | str,
        fft_size: int,
        step_hz: float | None,
        sweeps: int,
        dwell_ms: int,
        missing_db: float,
        antenna_tag: str | None,
        location_tag: str | None,
    ) -> ScanResult:
        try:
            import numpy as np
            from rtlsdr import RtlSdr
        except ImportError as exc:  # pragma: no cover - depends on optional deps
            raise SystemExit(
                "Real mode requires numpy and pyrtlsdr. Install with: pip install numpy pyrtlsdr"
            ) from exc

        if stop_hz <= start_hz:
            raise ValueError("stop_hz must be greater than start_hz")
        if bin_hz <= 0:
            raise ValueError("bin_hz must be positive")
        if sample_rate_hz <= 0:
            raise ValueError("sample_rate_hz must be positive")
        if fft_size <= 0:
            raise ValueError("fft_size must be positive")
        if sweeps <= 0:
            raise ValueError("sweeps must be positive")
        if dwell_ms < 0:
            raise ValueError("dwell_ms must be >= 0")

        step = step_hz or sample_rate_hz * 0.8
        n_bins = int(math.ceil((stop_hz - start_hz) / bin_hz))
        sum_bins = [0.0] * n_bins
        count_bins = [0] * n_bins
        max_bins = [float("-inf")] * n_bins

        sdr = RtlSdr()
        try:
            sdr.sample_rate = sample_rate_hz
            if gain_db == "auto":
                sdr.gain = "auto"
            else:
                sdr.gain = float(gain_db)

            window = np.hanning(fft_size)
            for _ in range(sweeps):
                center = start_hz + sample_rate_hz / 2.0
                while center < stop_hz:
                    sdr.center_freq = center
                    samples = sdr.read_samples(fft_size)
                    spectrum = np.fft.fftshift(np.fft.fft(samples * window))
                    power = 20 * np.log10(np.abs(spectrum) + 1e-12)
                    freqs = np.fft.fftshift(
                        np.fft.fftfreq(fft_size, d=1.0 / sample_rate_hz)
                    )
                    freqs = freqs + center

                    for freq_hz, power_db in zip(freqs, power):
                        if freq_hz < start_hz or freq_hz >= stop_hz:
                            continue
                        idx = int((freq_hz - start_hz) // bin_hz)
                        if idx < 0 or idx >= n_bins:
                            continue
                        sum_bins[idx] += float(power_db)
                        count_bins[idx] += 1
                        if power_db > max_bins[idx]:
                            max_bins[idx] = float(power_db)

                    if dwell_ms:
                        time.sleep(dwell_ms / 1000.0)
                    center += step
        finally:
            sdr.close()

        bins: list[ScanBin] = []
        for idx in range(n_bins):
            freq = start_hz + idx * bin_hz
            if count_bins[idx] == 0:
                avg_db = missing_db
                max_db = missing_db
            else:
                avg_db = sum_bins[idx] / count_bins[idx]
                max_db = max_bins[idx]
            bins.append(ScanBin(freq_hz=freq, avg_db=avg_db, max_db=max_db))

        return ScanResult(
            timestamp=ScanResult.now_iso(),
            start_hz=start_hz,
            stop_hz=stop_hz,
            bin_hz=bin_hz,
            bins=tuple(bins),
            antenna_tag=antenna_tag,
            location_tag=location_tag,
        )
