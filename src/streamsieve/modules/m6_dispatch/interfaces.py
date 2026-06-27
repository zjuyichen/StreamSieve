"""M6 protocol: review-queue dispatch."""
from __future__ import annotations

from typing import Protocol

from ...common.types import FrameDecision


class Dispatcher(Protocol):
    def dispatch(self, decision: FrameDecision, payload_ref: int | None) -> bool:
        """True = accepted; False = backpressure (caller applies its policy)."""
        ...
