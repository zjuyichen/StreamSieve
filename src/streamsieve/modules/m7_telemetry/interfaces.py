"""M7 protocol: telemetry sink."""
from __future__ import annotations

from typing import Protocol

from ...common.types import FrameDecision


class TelemetrySink(Protocol):
    def on_decision(self, decision: FrameDecision) -> None: ...
    def on_event(self, event: str, payload: dict) -> None: ...
