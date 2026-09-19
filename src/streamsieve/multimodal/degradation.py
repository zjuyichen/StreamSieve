"""Graceful degradation: any missing / low-confidence modality → force human escalation for that window (never assume safe).

Relation to M5: degradation signals are injected through existing force-review channels such as mask.overlay_mutation,
leaving the M5 safety-floor invariants untouched (Phase II reuses the same decision core).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DegradationPolicy:
    min_modalities: int = 2
    require_human_on_missing: bool = True

    def decide(self, available_modalities: list[str]) -> str:
        if len(available_modalities) >= self.min_modalities:
            return "proceed"
        return "escalate_human" if self.require_human_on_missing else "proceed_visual_only"
