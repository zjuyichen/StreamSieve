"""Anchor-frame management: the differential reference is the most recent frame that received a full safety check.

Rules (key to drift prevention):
- frames dispatched as REVIEW / FORCE_REVIEW / SAFETY_FLOOR / FAILSAFE become the new anchor (now covered);
- BYPASS frames do not update the anchor — drift keeps accumulating on the "anchor ↔ current" channel and cannot be diluted;
- a scene cut forces an anchor refresh even when bypassed (the old anchor is meaningless after a full scene change).
"""
from __future__ import annotations

from dataclasses import dataclass

from ...common.types import Descriptor, Outcome


@dataclass
class AnchorManager:
    anchor: Descriptor | None = None
    age_frames: int = 0

    def observe(self, desc: Descriptor, outcome: Outcome, scene_cut: bool) -> None:
        if outcome != Outcome.BYPASS or scene_cut:
            self.anchor = desc
            self.age_frames = 0
        else:
            self.age_frames += 1

    @property
    def current(self) -> Descriptor | None:
        return self.anchor
