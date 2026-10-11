"""M5 decision-core golden tests: cover design invariants INV1–INV4 one by one."""
from __future__ import annotations

import time

from streamsieve.common.types import FrameEnvelope, MaskSet, Mode, Outcome, Reason, SimilarityResult
from streamsieve.modules.m5_decision.decision import DecisionConfig, DecisionState, decide


def make_frame(seq: int = 0) -> FrameEnvelope:
    return FrameEnvelope(stream_id="t", seq=seq, pts_ns=seq * 16_666_667, t_ingest_ns=time.monotonic_ns(),
                         width=32, height=32, pixel_format="luma32")


def make_sig(fused: float = 0.0, quad_max: float = 0.0, scene_cut: bool = False) -> SimilarityResult:
    return SimilarityResult(fused=fused, dprev=fused, danchor=fused, mad=0.0, quad_q=(quad_max, 0, 0, 0),
                            scene_cut=scene_cut)


def run_seq(scores, *, cfg: DecisionConfig | None = None, masks=None, fps: float = 60.0):
    cfg = cfg or DecisionConfig()
    state = DecisionState()
    out = []
    for i, s in enumerate(scores):
        sig = make_sig(fused=s) if not isinstance(s, SimilarityResult) else s
        mask = masks[i] if masks else MaskSet()
        d, state = decide(frame=make_frame(i), sig=sig, mask=mask, state=state, cfg=cfg,
                          config_hash="test", frame_dt_s=1 / fps)
        out.append(d)
    return out


def test_static_stream_bypasses_then_hits_safety_floor():
    """INV1: dispatch frame gap ≤ bypass_streak_max_frames.

    With max=5: frames 0–3 bypass; frame 4 hits the safety floor (gap 5); frames 5–8 bypass; frame 9 triggers again.
    """
    cfg = DecisionConfig(bypass_streak_max_frames=5, bypass_streak_max_seconds=99.0, keepalive_every_seconds=99.0)
    ds = run_seq([0.001] * 12, cfg=cfg)
    outcomes = [d.outcome for d in ds]
    assert outcomes[0] == Outcome.BYPASS
    assert outcomes[4] == Outcome.SAFETY_FLOOR
    assert Reason.STREAK_FRAMES.value in ds[4].reasons
    assert outcomes[9] == Outcome.SAFETY_FLOOR
    # any adjacent dispatch gap ≤ the cap
    dispatched = [i for i, o in enumerate(outcomes) if o != Outcome.BYPASS]
    gaps = [b - a for a, b in zip(dispatched, dispatched[1:])]
    assert all(g <= cfg.bypass_streak_max_frames for g in gaps)


def test_scene_cut_forces_review():
    ds = run_seq([make_sig(fused=0.4, scene_cut=True)])
    assert ds[0].outcome == Outcome.FORCE_REVIEW
    assert Reason.SCENE_CUT.value in ds[0].reasons


def test_overlay_mutation_forces_review_even_when_fused_low():
    ds = run_seq([SimilarityResult(fused=0.0001, dprev=0, danchor=0, mad=0)],
                 masks=[MaskSet(overlay_mutation=True)])
    assert ds[0].outcome == Outcome.FORCE_REVIEW
    assert Reason.OVERLAY_MUTATION.value in ds[0].reasons


def test_quadrant_max_forces_review_independent_of_adaptive():
    ds = run_seq([make_sig(fused=0.0, quad_max=0.9)])
    assert ds[0].outcome == Outcome.FORCE_REVIEW
    assert Reason.STRONG_QUADRANT_DELTA.value in ds[0].reasons


def test_gray_zone_hysteresis_confirm():
    cfg = DecisionConfig(hysteresis_frames=2, t_gray_upper=0.06, t_bypass=0.02)
    ds = run_seq([0.03, 0.03, 0.03], cfg=cfg)
    assert ds[0].outcome == Outcome.BYPASS and Reason.GRAY_PENDING.value in ds[0].reasons
    assert ds[1].outcome == Outcome.REVIEW and Reason.HYSTERESIS_CONFIRMED.value in ds[1].reasons


def test_keepalive_triggers_within_seconds_bound():
    cfg = DecisionConfig(bypass_streak_max_frames=10_000, bypass_streak_max_seconds=100.0,
                         keepalive_every_seconds=0.05)
    ds = run_seq([0.001] * 10, cfg=cfg, fps=60.0)
    triggered = [d for d in ds if Reason.KEEPALIVE.value in d.reasons]
    assert triggered, "keepalive sampling must fire (INV2 time cap)"


def test_failsafe_mode_dispatches_everything():
    cfg = DecisionConfig()
    state = DecisionState(mode=Mode.FAILSAFE_BYPASS)
    d, state = decide(frame=make_frame(), sig=make_sig(0.0), mask=MaskSet(), state=state, cfg=cfg,
                      config_hash="test")
    assert d.outcome == Outcome.FAILSAFE
    assert Reason.FAILSAFE_MODE.value in d.reasons
