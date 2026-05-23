"""Mask composition and sensitivity weights.

- region → sensitivity weight (overlay_sensitivity): active overlay quadrants are weighted in M4/M5;
- conservative mode (detector failure): treat every region as text (force review).
"""
from __future__ import annotations

from ...common.types import MaskSet, Region

CONSERVATIVE = MaskSet(regions=(), overlay_mutation=True, overlay_score=1.0)


def conservative_mask() -> MaskSet:
    return CONSERVATIVE


def region_weight(region: Region, base: float) -> float:
    """Higher textiness and larger regions → higher weight (used by score fusion)."""
    return base * (1.0 + region.textiness)
