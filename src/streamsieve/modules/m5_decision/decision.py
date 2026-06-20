"""M5 adaptive frame-decision filter — the decision core (single source of truth for safety logic).

Decision order (safety priority, highest first):
  0) FAILSAFE_BYPASS mode        → Outcome.FAILSAFE (dispatch everything; G9)
  1) force-review signals (any hit)  → FORCE_REVIEW
     - mask.overlay_mutation         overlay (danmaku/caption) mutation
     - quad_max ≥ t_force            strong local quadrant change (not diluted by the mean)
     - scene_cut                     scene change
  2) safety floors (checked before any bypass) → SAFETY_FLOOR
     - consecutive-bypass interval reaches bypass_streak_max_frames (frame cap)
     - consecutive-bypass interval reaches bypass_streak_max_seconds (time cap)
     - keepalive sampling due (keepalive_every_seconds)
  3) tiered scoring              → BYPASS | REVIEW
     - score ≤ t_bypass×k         redundant (k = adaptive factor; only applied here)
     - score < t_gray_upper       gray zone: only confirmed as REVIEW after hysteresis_frames consecutive frames
     - score ≥ t_gray_upper       gradual change → REVIEW

Design invariants (asserted one-by-one in tests/unit/test_decision_golden.py):
  INV1 frame gap between dispatches ≤ bypass_streak_max_frames
  INV2 time gap between dispatches ≤ max(bypass_streak_max_seconds, keepalive_every_seconds)
  INV3 the force-review channel is unaffected by the adaptive factor
  INV4 lower thresholds ⇒ monotone non-decreasing recall (basis for the calibration script)

Note: `cfg.adaptive` holds mutable state (EWMA); each stream MUST hold its own copy
(`clone_decision_config` or deepcopy; run_reference already handles this).
"""
from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Tuple

from ...common.clock import mono_ns
from ...common.types import FrameDecision, FrameEnvelope, MaskSet, Mode, Outcome, Reason, SimilarityResult
from .thresholds import AdaptiveThreshold


@dataclass
class DecisionConfig:
    t_bypass: float = 0.020
    t_gray_upper: float = 0.060
    t_force: float = 0.120
    hysteresis_frames: int = 2
    scene_cut_threshold: float = 0.250
    bypass_streak_max_frames: int = 150
    bypass_streak_max_seconds: float = 2.5
    keepalive_every_seconds: float = 5.0
    overlay_sensitivity: float = 1.5
    adaptive: AdaptiveThreshold = field(default_factory=AdaptiveThreshold)


@dataclass
class DecisionState:
    """One per stream (owned by the engine; the caller persists the returned new state)."""

    bypass_streak_frames: int = 0     # consecutive bypassed frames since the last dispatch
    gray_run: int = 0                 # consecutive gray-zone frames (hysteresis)
    frames_since_review: int = 0
    seconds_since_review: float = 0.0
    seconds_since_keepalive: float = 0.0
    mode: Mode = Mode.NORMAL


def clone_decision_config(cfg: DecisionConfig) -> DecisionConfig:
    """Produce an independent config copy for one stream (isolates the adaptive EWMA state)."""
    return copy.deepcopy(cfg)


def decide(
    *,
    frame: FrameEnvelope,
    sig: SimilarityResult,
    mask: MaskSet,
    state: DecisionState,
    cfg: DecisionConfig,
    config_hash: str,
    frame_dt_s: float = 1.0 / 60.0,
    ts_decision_ns: int | None = None,
) -> Tuple[FrameDecision, DecisionState]:
    """Pure decision function: returns (decision, new_state)."""
    t_dec = ts_decision_ns if ts_decision_ns is not None else mono_ns()
    dt = max(frame_dt_s, 1e-6)

    # ---------- 0) fail-safe: dispatch everything ----------
    if state.mode == Mode.FAILSAFE_BYPASS:
        decision = _emit(frame, Outcome.FAILSAFE, sig, mask, cfg, config_hash,
                         [Reason.FAILSAFE_MODE], t_dec, state.mode)
        return decision, _advance_review(state, dt)

    # ---------- 1) force-review signals (safety channel; adaptive factor not applied) ----------
    reasons: list[Reason] = []
    if mask.overlay_mutation:
        reasons.append(Reason.OVERLAY_MUTATION)
    if sig.quad_max >= cfg.t_force:
        reasons.append(Reason.STRONG_QUADRANT_DELTA)
    if sig.scene_cut:
        reasons.append(Reason.SCENE_CUT)
    if reasons:
        decision = _emit(frame, Outcome.FORCE_REVIEW, sig, mask, cfg, config_hash, reasons, t_dec, state.mode)
        return decision, _advance_review(state, dt)

    score = sig.fused
    cfg.adaptive.update(score)  # affects only the benefit side (t_bypass)

    # ---------- 2) safety floors (before any bypass; hard interval caps) ----------
    if state.bypass_streak_frames + 1 >= cfg.bypass_streak_max_frames:
        decision = _emit(frame, Outcome.SAFETY_FLOOR, sig, mask, cfg, config_hash,
                         [Reason.STREAK_FRAMES], t_dec, state.mode)
        return decision, _advance_review(state, dt)
    if state.seconds_since_review + dt >= cfg.bypass_streak_max_seconds:
        decision = _emit(frame, Outcome.SAFETY_FLOOR, sig, mask, cfg, config_hash,
                         [Reason.STREAK_SECONDS], t_dec, state.mode)
        return decision, _advance_review(state, dt)
    if state.seconds_since_keepalive + dt >= cfg.keepalive_every_seconds:
        decision = _emit(frame, Outcome.SAFETY_FLOOR, sig, mask, cfg, config_hash,
                         [Reason.KEEPALIVE], t_dec, state.mode)
        return decision, _advance_review(state, dt)

    # ---------- 3) tiered scoring ----------
    t_bypass_eff = cfg.t_bypass * cfg.adaptive.factor
    if score <= t_bypass_eff:
        decision = _emit(frame, Outcome.BYPASS, sig, mask, cfg, config_hash,
                         [Reason.REDUNDANT], t_dec, state.mode)
        return decision, _advance_bypass(state, dt, gray_delta_reset=True)
    if score < cfg.t_gray_upper:
        if state.gray_run + 1 >= cfg.hysteresis_frames:
            decision = _emit(frame, Outcome.REVIEW, sig, mask, cfg, config_hash,
                             [Reason.HYSTERESIS_CONFIRMED], t_dec, state.mode)
            return decision, _advance_review(state, dt)
        decision = _emit(frame, Outcome.BYPASS, sig, mask, cfg, config_hash,
                         [Reason.GRAY_PENDING], t_dec, state.mode)
        return decision, _advance_bypass(state, dt, gray_delta=1)
    decision = _emit(frame, Outcome.REVIEW, sig, mask, cfg, config_hash,
                     [Reason.GRADUAL_CHANGE], t_dec, state.mode)
    return decision, _advance_review(state, dt)


# ------------------------- internal helpers -------------------------

def _emit(frame: FrameEnvelope, outcome: Outcome, sig: SimilarityResult, mask: MaskSet,
          cfg: DecisionConfig, config_hash: str, reasons: list[Reason], t_dec: int, mode: Mode) -> FrameDecision:
    return FrameDecision(
        stream_id=frame.stream_id,
        seq=frame.seq,
        outcome=outcome,
        score=sig.fused,
        mode=mode,
        config_hash=config_hash,
        t_ingest_ns=frame.t_ingest_ns,
        t_decision_ns=t_dec,
        reasons=tuple(r.value for r in reasons),
        overlay_mutation=mask.overlay_mutation,
        quadrant_max=sig.quad_max,
    )


def _advance_review(state: DecisionState, dt: float) -> DecisionState:
    state.bypass_streak_frames = 0
    state.gray_run = 0
    state.frames_since_review = 0
    state.seconds_since_review = 0.0
    state.seconds_since_keepalive = 0.0
    return state


def _advance_bypass(state: DecisionState, dt: float, *, gray_delta: int = 0,
                    gray_delta_reset: bool = False) -> DecisionState:
    state.bypass_streak_frames += 1
    state.frames_since_review += 1
    state.seconds_since_review += dt
    state.seconds_since_keepalive += dt
    if gray_delta_reset:
        state.gray_run = 0
    else:
        state.gray_run += gray_delta
    return state
