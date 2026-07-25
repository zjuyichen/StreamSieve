"""Reference implementation: pure-Python single-threaded end-to-end pipeline (correctness verification / teaching; not the performance path).

Purpose:
- validates reduction ratio / force-review channel / safety floors / anchor behavior on synthetic streams from day one;
- engine behind tests/integration and scripts/demo_reference.py;
- shares the same M2/M4/M5 reference functions as the production path so semantics stay identical.

Data flow: 32×32 luma → pHash/quadrants → differential fusion → M5 decision → anchor/stats.
Production swap points: M2/M4 move to native kernels; M1/M3/M6/M7 get full implementations; the decision core (M5) stays unchanged.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Iterable, Optional

from ..common.types import Descriptor, FrameEnvelope, MaskSet, Outcome
from ..modules.m2_features.phash import phash64, quadrant_hashes
from ..modules.m4_similarity.anchor import AnchorManager
from ..modules.m4_similarity.scoring import Weights, fuse
from ..modules.m4_similarity.structural import block_mean_diff, ssim_lite
from ..modules.m5_decision.decision import DecisionConfig, DecisionState, decide


@dataclass
class ReferenceStats:
    total: int = 0
    by_outcome: dict = field(default_factory=dict)
    max_gap_frames: int = 0          # max frame gap between two dispatches (INV1)
    max_gap_seconds: float = 0.0     # max time gap between two dispatches (INV2)
    dispatched_seqs: list = field(default_factory=list)

    @property
    def reduce_ratio(self) -> float:
        return self.by_outcome.get("BYPASS", 0) / self.total if self.total else 0.0

    def note(self, outcome: Outcome) -> None:
        self.by_outcome[outcome.value] = self.by_outcome.get(outcome.value, 0) + 1


def _descriptor(luma) -> Descriptor:
    return Descriptor(phash64=phash64(luma), quad_h=quadrant_hashes(luma))


def run_reference(
    frames: Iterable[FrameEnvelope],
    *,
    cfg: Optional[DecisionConfig] = None,
    fps: float = 60.0,
    config_hash: str = "reference",
    masker=None,
) -> ReferenceStats:
    # per-stream copy (isolates adaptive EWMA state; see decision.clone_decision_config)
    cfg = copy.deepcopy(cfg) if cfg is not None else DecisionConfig()
    state = DecisionState()
    anchor = AnchorManager()
    stats = ReferenceStats()
    weights = Weights()
    prev_luma = None
    prev_desc: Optional[Descriptor] = None
    last_dispatch_seq: Optional[int] = None

    for frame in frames:
        luma = frame.luma_small
        if luma is None:
            continue
        desc = _descriptor(luma)
        mad = block_mean_diff(prev_luma, luma) if prev_luma is not None else 0.0
        ssim = ssim_lite(prev_luma, luma) if prev_luma is not None else 1.0
        sig = fuse(desc=desc, prev=prev_desc, anchor=anchor.current, mad=mad, ssim=ssim,
                   weights=weights, scene_cut_threshold=cfg.scene_cut_threshold)
        mask = masker.mask(frame) if masker is not None else MaskSet()
        decision, state = decide(
            frame=frame, sig=sig, mask=mask, state=state, cfg=cfg,
            config_hash=config_hash, frame_dt_s=1.0 / fps,
        )
        stats.total += 1
        stats.note(decision.outcome)

        dispatched = decision.outcome != Outcome.BYPASS
        anchor.observe(desc, decision.outcome, sig.scene_cut)
        if dispatched:
            if last_dispatch_seq is not None:
                gap = frame.seq - last_dispatch_seq
                stats.max_gap_frames = max(stats.max_gap_frames, gap)
                stats.max_gap_seconds = max(stats.max_gap_seconds, gap / fps)
            last_dispatch_seq = frame.seq
            stats.dispatched_seqs.append(frame.seq)
        prev_luma, prev_desc = luma, desc

    return stats
