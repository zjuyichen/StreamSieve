"""Hamming distance / normalization (pure-Python reference implementation)."""
from __future__ import annotations


def popcount(x: int) -> int:
    try:
        return x.bit_count()  # py>=3.8 on some environments
    except AttributeError:  # pragma: no cover
        return bin(x).count("1")


def hamming(bits_a: int, bits_b: int, width: int) -> float:
    """Normalized Hamming distance ∈ [0,1] (0 = identical)."""
    if width <= 0:
        raise ValueError("width must be > 0")
    return popcount(bits_a ^ bits_b) / float(width)


def hamming64(a: int, b: int) -> float:
    return hamming(a, b, 64)


def hamming16(a: int, b: int) -> float:
    return hamming(a, b, 16)
