"""Synthetic frame fixtures: 32x32 luma patterns (pure Python, no third-party deps)."""
from __future__ import annotations

import pytest


def gradient(level: int) -> list[list[float]]:
    return [[(x * 3 + y * 2 + level) % 256 for x in range(32)] for y in range(32)]


def checker(shift: int) -> list[list[float]]:
    return [[255 if ((x // 4 + y // 4 + shift) % 2 == 0) else 0 for x in range(32)] for y in range(32)]


def patch(base: list[list[float]], x0: int, y0: int, size: int = 8, value: float = 255.0) -> list[list[float]]:
    out = [row[:] for row in base]
    for y in range(y0, min(y0 + size, 32)):
        for x in range(x0, min(x0 + size, 32)):
            out[y][x] = value
    return out


@pytest.fixture()
def static_frames():
    return [gradient(40) for _ in range(16)]


@pytest.fixture()
def scene_cut_frames():
    return [gradient(40) for _ in range(8)] + [checker(0) for _ in range(8)]


@pytest.fixture()
def moving_patch_frames():
    frames = [gradient(40) for _ in range(8)]
    base = gradient(40)
    for i in range(8):
        frames.append(patch(base, (i * 3) % 24, 8, size=6))
    return frames
