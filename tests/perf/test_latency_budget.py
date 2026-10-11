"""Performance regression gate: loose latency check for the reference implementation (the production gate runs in cloud-profile CI)."""
from __future__ import annotations

import time

import pytest

from streamsieve.modules.m1_normalization.sources.synthetic import SyntheticPattern, SyntheticSource
from streamsieve.modules.m5_decision.decision import DecisionConfig
from streamsieve.pipeline.reference import run_reference


def _static(i, h, w):
    return [[(x * 3 + y * 2 + 40) % 256 for x in range(w)] for y in range(h)]


@pytest.mark.perf
def test_reference_pipeline_local_smoke():
    """Reference implementation (pure Python) smoke test only: 60 frames should stay far below 60×45 ms."""
    cfg = DecisionConfig()
    src = SyntheticSource(SyntheticPattern("static", _static), frames=60)
    t0 = time.perf_counter()
    stats = run_reference(src.frames(), cfg=cfg)
    dt_ms = (time.perf_counter() - t0) * 1000
    assert stats.total == 60
    assert dt_ms < 60 * 45, "the reference per-frame average must stay below 45 ms (even in pure Python)"
