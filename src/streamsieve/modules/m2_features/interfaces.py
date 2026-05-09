"""M2 protocol: feature extractor."""
from __future__ import annotations

from typing import Protocol

from ...common.types import Descriptor, FrameEnvelope


class FeatureExtractor(Protocol):
    """Cascading implementations allowed (embedding only fires in the gray zone)."""

    def extract(self, frame: FrameEnvelope, *, want_embedding: bool = False) -> Descriptor:
        ...
