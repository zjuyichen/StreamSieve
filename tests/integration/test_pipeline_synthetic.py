"""End-to-end reference implementation (synthetic streams): reduction ratio, force-review channel, and safety floors, all covered."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from streamsieve.modules.m1_normalization.sources.synthetic import SyntheticPattern, SyntheticSource
from streamsieve.modules.m3_masking.overlay_detector import OverlayWatcher
from streamsieve.modules.m5_decision.decision import DecisionConfig
from streamsieve.pipeline.reference import run_reference


def _static(i, h, w):
    return [[(x * 3 + y * 2 + 40) % 256 for x in range(w)] for y in range(h)]


def _cut(i, h, w):
    if i < 40:
        return _static(i, h, w)
    return [[255 if ((x // 4 + y // 4) % 2 == 0) else 0 for x in range(w)] for y in range(h)]


def test_static_stream_high_reduction_and_floor():
    cfg = DecisionConfig(bypass_streak_max_frames=20, bypass_streak_max_seconds=99.0,
                         keepalive_every_seconds=99.0)
    src = SyntheticSource(SyntheticPattern("static", _static), frames=60)
    stats = run_reference(src.frames(), cfg=cfg)
    assert stats.total == 60
    assert stats.by_outcome.get("BYPASS", 0) >= 45          # static-stream reduction ≥75%
    assert stats.by_outcome.get("SAFETY_FLOOR", 0) >= 2     # safety floor engaged (INV1)
    assert stats.max_gap_frames <= cfg.bypass_streak_max_frames


def test_scene_cut_is_dispatched():
    cfg = DecisionConfig()
    src = SyntheticSource(SyntheticPattern("cut", _cut), frames=80)
    stats = run_reference(src.frames(), cfg=cfg)
    # the scene-cut frame (around seq=40) must be dispatched
    assert any(39 <= s <= 41 for s in stats.dispatched_seqs)


def test_overlay_mutation_forces_review_path():
    cfg = DecisionConfig(bypass_streak_max_frames=10_000, bypass_streak_max_seconds=999,
                         keepalive_every_seconds=999)
    # danmaku text blocks flip at high frequency from frame 10 (simulating scrolling comments)
    def _danmaku(i, h, w):
        base = [[200 for _ in range(w)] for _ in range(h)]
        if i >= 10:
            phase = i % 2
            for y in range(2, 8):
                for x in range(2, 30):
                    base[y][x] = 0 if (x + phase) % 2 == 0 else 255
        return base

    src = SyntheticSource(SyntheticPattern("danmaku", _danmaku), frames=24)
    stats = run_reference(src.frames(), cfg=cfg, masker=OverlayWatcher(grid=(1, 1), textiness_threshold=0.1))
    forced = [s for s in stats.dispatched_seqs if s >= 10]
    assert forced, "overlay mutation must trigger force review (M3→M5 channel)"
