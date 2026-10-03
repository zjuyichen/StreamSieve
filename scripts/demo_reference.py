#!/usr/bin/env python3
"""Reference pipeline demo: shows reduction ratio / force-review channel / safety floors / anchor behavior on synthetic streams.

Usage: PYTHONPATH=src python3 scripts/demo_reference.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from streamsieve.modules.m1_normalization.sources.synthetic import SyntheticPattern, SyntheticSource
from streamsieve.modules.m3_masking.overlay_detector import OverlayWatcher
from streamsieve.modules.m5_decision.decision import DecisionConfig
from streamsieve.pipeline.reference import run_reference


def _static(i, h, w):
    return [[(x * 3 + y * 2 + 40) % 256 for x in range(w)] for y in range(h)]


def _mixed(i, h, w):
    if i < 60:
        return _static(i, h, w)
    if i < 120:  # moving square
        base = [[60 for _ in range(w)] for _ in range(h)]
        x0 = (i * 2) % 24
        for y in range(8, 16):
            for x in range(x0, x0 + 6):
                base[y][x] = 220
        return base
    return [[255 if ((x // 4 + y // 4) % 2 == 0) else 0 for x in range(w)] for y in range(h)]  # scene cut


def _danmaku(i, h, w):
    base = [[200 for _ in range(w)] for _ in range(h)]
    if i >= 30:
        phase = i % 2
        for y in range(4, 10):
            for x in range(2, 30):
                base[y][x] = 0 if (x + phase) % 2 == 0 else 255
    return base


def report(name: str, stats) -> None:
    print(f"\n=== {name} ===")
    print(f"total frames: {stats.total}")
    for k, v in sorted(stats.by_outcome.items()):
        print(f"  {k:14s}: {v}")
    print(f"  reduction ratio (BYPASS share): {stats.reduce_ratio:.1%}")
    print(f"  max dispatch gap: {stats.max_gap_frames} frames / {stats.max_gap_seconds:.2f}s")


def main() -> None:
    cfg = DecisionConfig(bypass_streak_max_frames=45, bypass_streak_max_seconds=99,
                         keepalive_every_seconds=99)

    s1 = SyntheticSource(SyntheticPattern("static", _static), frames=120, stream_id="static")
    report("static stream (expect high reduction + periodic safety floors)", run_reference(s1.frames(), cfg=cfg))

    s2 = SyntheticSource(SyntheticPattern("mixed", _mixed), frames=180, stream_id="mixed")
    report("mixed stream (static → motion → scene cut)", run_reference(s2.frames(), cfg=cfg))

    s3 = SyntheticSource(SyntheticPattern("danmaku", _danmaku), frames=60, stream_id="danmaku")
    report("danmaku overlay-mutation stream (expect force reviews)",
           run_reference(s3.frames(), cfg=cfg, masker=OverlayWatcher(grid=(1, 1), textiness_threshold=0.1)))

    print("\nNote: this demo is the pure-Python reference implementation (correctness/teaching); the production performance path is described in DESIGN.md §7.")


if __name__ == "__main__":
    main()
