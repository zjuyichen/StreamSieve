"""M5 protocol: adaptive frame-decision filter."""
from __future__ import annotations

from typing import Protocol

from ...common.types import FrameDecision, FrameEnvelope, MaskSet, SimilarityResult


class DecisionFilter(Protocol):
    def decide(
        self, frame: FrameEnvelope, sig: SimilarityResult, mask: MaskSet, *, mode
    ) -> FrameDecision:
        ...
