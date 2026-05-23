"""M3 overlay detection and mutation watch ("text changed" detection without OCR).

Algorithm (on the 1/8 pyramid):
1. tile textiness = edge density × stroke consistency (Sobel approximation + threshold);
2. sliding-window voting → stable regions (danmaku/chat/captions/game UI) are registered and tracked;
3. overlay mutation watch: binarize registered regions → region hash; hash change > ε → overlay_mutation=True.

The pure-Python reference provides minimal tile textiness + per-frame region-hash comparison;
production replaces it with a native kernel behind the same interface.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from ...common.hashing import content_hash
from ...common.types import FrameEnvelope, MaskSet, Region, RegionKind


def _tile_textiness(tile: Sequence[Sequence[float]]) -> float:
    """Minimal textiness: fraction of active neighboring differences along rows (text = high-frequency strokes, normalized to [0,1])."""
    h, w = len(tile), len(tile[0])
    active = 0
    total = 0
    for y in range(h - 1):
        for x in range(w - 1):
            d = abs(tile[y][x + 1] - tile[y][x]) + abs(tile[y + 1][x] - tile[y][x])
            total += 1
            if d > 60:  # empirical threshold (grayscale delta)
                active += 1
    return active / max(total, 1)


@dataclass
class OverlayWatcher:
    """Region registry + mutation watch. Lifetime = one stream."""

    grid: tuple[int, int] = (4, 4)          # reference uses 4x4 (production: 16x9)
    textiness_threshold: float = 0.25
    hash_epsilon: float = 0.02
    regions: list[Region] = field(default_factory=list)
    _last_region_hash: dict[tuple[int, int, int, int], int] = field(default_factory=dict)

    def mask(self, frame: FrameEnvelope) -> MaskSet:
        luma = frame.luma_small
        if luma is None:
            return MaskSet()
        gh, gw = self.grid
        h, w = len(luma), len(luma[0])
        th, tw = max(h // gh, 1), max(w // gw, 1)
        mutation = False
        regions: list[Region] = []
        for gy in range(gh):
            for gx in range(gw):
                tile = [row[gx * tw : (gx + 1) * tw] for row in luma[gy * th : (gy + 1) * th]]
                t = _tile_textiness(tile)
                if t >= self.textiness_threshold:
                    rect = (gx, gy, tw, th)
                    regions.append(Region(kind=RegionKind.CAPTION, x=rect[0], y=rect[1], w=tw, h=th, textiness=t))
                    binar = [[1 if (v > 128) else 0 for v in row] for row in tile]
                    hsh = content_hash(binar)
                    prev = self._last_region_hash.get(rect)
                    if prev is not None and hsh != prev:
                        mutation = True
                    self._last_region_hash[rect] = hsh
        self.regions = regions
        return MaskSet(regions=tuple(regions), overlay_mutation=mutation,
                       overlay_score=sum(r.textiness for r in regions) / max(len(regions), 1))
