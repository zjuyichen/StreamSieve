"""Structural difference: block-mean difference (MAD) and SSIM-lite.

- mad: normalized 8×8 block-mean absolute difference on the 1/8 pyramid (|Δ|/255, averaged over blocks);
- ssim_lite: simplified SSIM (global mean/variance approximation); production may swap in a windowed version.
Both read only the 1/8 pyramid, at O(pixels/64).
"""
from __future__ import annotations

from typing import Sequence


def block_mean_diff(a: Sequence[Sequence[float]], b: Sequence[Sequence[float]], blocks: int = 8) -> float:
    """8×8 block-mean average absolute difference, normalized to [0,1]."""
    h = len(a)
    w = len(a[0])
    bh, bw = max(h // blocks, 1), max(w // blocks, 1)
    total = 0.0
    n = 0
    for by in range(0, h - bh + 1, bh):
        for bx in range(0, w - bw + 1, bw):
            ma = sum(sum(row[bx : bx + bw]) for row in a[by : by + bh]) / (bh * bw)
            mb = sum(sum(row[bx : bx + bw]) for row in b[by : by + bh]) / (bh * bw)
            total += abs(ma - mb)
            n += 1
    return (total / max(n, 1)) / 255.0


def ssim_lite(a: Sequence[Sequence[float]], b: Sequence[Sequence[float]]) -> float:
    """Simplified SSIM ∈ [-1,1] based on global mean/variance."""
    flat_a = [v for row in a for v in row]
    flat_b = [v for row in b for v in row]
    n = len(flat_a)
    ma = sum(flat_a) / n
    mb = sum(flat_b) / n
    va = sum((x - ma) ** 2 for x in flat_a) / n
    vb = sum((x - mb) ** 2 for x in flat_b) / n
    cov = sum((x - ma) * (y - mb) for x, y in zip(flat_a, flat_b)) / n
    c1, c2 = (0.01 * 255) ** 2, (0.03 * 255) ** 2
    return ((2 * ma * mb + c1) * (2 * cov + c2)) / ((ma * ma + mb * mb + c1) * (va + vb + c2))
