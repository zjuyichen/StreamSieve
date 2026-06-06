"""Fused-score formula (the single entry point for M4 SimilarityResult).

fused = w_prev·dprev + w_anchor·danchor + w_mad·mad + w_ssim·(1−ssim_lite)
All inputs are normalized to [0,1]; weights come from config.similarity.weights.
Quadrant OR: quad_max is emitted separately for the M5 force-review channel (not diluted by the mean).
"""
from __future__ import annotations

from dataclasses import dataclass

from ...common.types import Descriptor, SimilarityResult
from .hamming import hamming16, hamming64


@dataclass
class Weights:
    prev: float = 0.45
    anchor: float = 0.30
    mad: float = 0.15
    ssim: float = 0.10


def fuse(
    *,
    desc: Descriptor,
    prev: Descriptor | None,
    anchor: Descriptor | None,
    mad: float,
    ssim: float,
    weights: Weights,
    scene_cut_threshold: float = 0.25,
) -> SimilarityResult:
    dprev = hamming64(desc.phash64, prev.phash64) if prev else 0.0
    danchor = hamming64(desc.phash64, anchor.phash64) if anchor else dprev

    if prev:
        quad_q = tuple(
            hamming16(desc.quad_h[i], prev.quad_h[i]) for i in range(4)
        )
    else:
        quad_q = (0.0, 0.0, 0.0, 0.0)

    fused = (
        weights.prev * dprev
        + weights.anchor * danchor
        + weights.mad * max(min(mad, 1.0), 0.0)
        + weights.ssim * max(min(1.0 - ssim, 1.0), 0.0) / 2.0  # ssim∈[-1,1] → [0,1]
    )
    fused = max(min(fused, 1.0), 0.0)
    scene_cut = fused >= scene_cut_threshold or max(quad_q) >= 0.5
    return SimilarityResult(
        fused=fused, dprev=dprev, danchor=danchor, mad=mad, quad_q=quad_q, scene_cut=scene_cut
    )
