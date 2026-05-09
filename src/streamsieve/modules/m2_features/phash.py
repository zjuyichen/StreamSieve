"""64-bit pHash + quadrant hashes — pure-Python reference implementation (correctness/teaching; production uses native kernels).

Algorithm (matches module M2):
1. input: 32×32 luma on the 1/8 pyramid (caller guarantees dimensions);
2. partial DCT: compute only the low-frequency keep×keep block (P_keep @ X @ P_keepᵀ; no full 32×32 DCT);
3. threshold at the median of the low-frequency block → keep×keep-bit hash;
4. quadrants: four 16×16 blocks, each mapped to a 4×4 low-frequency block → 16 bits per quadrant (order: TL, TR, BL, BR).

Engineering notes:
- no numpy (avoids behavior drift across platform BLAS implementations); pure Python is for tests only;
- the production performance path is the native/ kernel (Rust/C++ + SIMD) with identical interface and semantics.
"""
from __future__ import annotations

import math
from typing import Sequence


def _partial_dct_matrix(n: int, keep: int) -> list[list[float]]:
    """Partial DCT matrix P: keep×n (rows k=0..keep-1, columns i=0..n-1)."""
    m = [[0.0] * n for _ in range(keep)]
    for k in range(keep):
        scale = math.sqrt(1.0 / n) if k == 0 else math.sqrt(2.0 / n)
        for i in range(n):
            m[k][i] = math.cos(math.pi * (2 * i + 1) * k / (2 * n)) * scale
    return m


_P8 = _partial_dct_matrix(32, 8)   # frame level: 32×32 → 8×8 low frequency
_P4 = _partial_dct_matrix(16, 4)   # quadrant level: 16×16 → 4×4 low frequency


def _lowfreq_block(x: Sequence[Sequence[float]], p: list[list[float]]) -> list[list[float]]:
    """Z = P @ X @ Pᵀ (keep×keep low-frequency block)."""
    keep, n = len(p), len(p[0])
    y = [[sum(p[k][i] * x[i][j] for i in range(n)) for j in range(n)] for k in range(keep)]
    z = [[sum(y[i][k] * p[j][k] for k in range(n)) for j in range(keep)] for i in range(keep)]
    return z


def _bits_from_block(z: list[list[float]]) -> int:
    flat = [v for row in z for v in row]
    med = sorted(flat)[len(flat) // 2]
    bits = 0
    for idx, v in enumerate(flat):
        if v > med:
            bits |= 1 << idx
    return bits


def _check_32x32(luma: Sequence[Sequence[float]]) -> None:
    if len(luma) != 32 or len(luma[0]) != 32:
        raise ValueError("this function requires 32x32 luma")


def phash64(luma32: Sequence[Sequence[float]]) -> int:
    """32×32 luma → 64-bit pHash."""
    _check_32x32(luma32)
    return _bits_from_block(_lowfreq_block(luma32, _P8))


def quadrant_hashes(luma32: Sequence[Sequence[float]]) -> tuple[int, int, int, int]:
    """Four 16×16 quadrants → four 16-bit hashes, order: TL, TR, BL, BR."""
    _check_32x32(luma32)
    quads = (
        [row[:16] for row in luma32[:16]],
        [row[16:] for row in luma32[:16]],
        [row[:16] for row in luma32[16:]],
        [row[16:] for row in luma32[16:]],
    )
    return tuple(_bits_from_block(_lowfreq_block(q, _P4)) for q in quads)  # type: ignore[return-value]
