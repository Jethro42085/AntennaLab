from __future__ import annotations

from antennalab.core.plugins import InstrumentPlugin
from antennalab.instruments.rtlsdr import RTLSDRPlugin


def get_instrument_plugins() -> list[InstrumentPlugin]:
    return [RTLSDRPlugin()]
