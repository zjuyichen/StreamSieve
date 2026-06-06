"""M4 protocol: differential similarity engine."""
from __future__ import annotations

from typing import Protocol

from ...common.types import Descriptor, FrameEnvelope, SimilarityResult


class SimilarityEngine(Protocol):
    def compare(
        self, frame: FrameEnvelope, desc: Descriptor, prev: Descriptor | None, anchor: Descriptor | None
    ) -> SimilarityResult:
        ...
