from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class PluginInfo:
    name: str
    kind: str
    description: str


@dataclass(frozen=True)
class HealthCheck:
    ok: bool
    status: str
    detail: str


class InstrumentPlugin(Protocol):
    def info(self) -> PluginInfo:
        ...

    def healthcheck(self, config: dict) -> HealthCheck:
        ...
