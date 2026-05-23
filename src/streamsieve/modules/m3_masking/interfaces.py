"""M3 protocol: risk-region masker."""
from __future__ import annotations

from typing import Protocol

from ...common.types import FrameEnvelope, MaskSet


class Masker(Protocol):
    def mask(self, frame: FrameEnvelope) -> MaskSet:
        ...
