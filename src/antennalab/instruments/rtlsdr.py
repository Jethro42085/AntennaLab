from __future__ import annotations

from antennalab.analysis.spectrum import ScanSimulator
from antennalab.core.models import ScanResult
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
