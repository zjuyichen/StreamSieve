"""End-to-end data contracts (single source of truth).

All modules interact only through the types defined here; the external JSON contract lives in
configs/schemas/frame_decision.schema.json (the two must evolve together).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional, Sequence, Tuple


class Outcome(str, Enum):
    """Per-frame decision outcomes."""

    BYPASS = "BYPASS"                # visually redundant: skip heavy safety inference
    REVIEW = "REVIEW"                # dispatch (platform classifier / human review queue)
    FORCE_REVIEW = "FORCE_REVIEW"    # forced dispatch (a force-review signal fired)
    SAFETY_FLOOR = "SAFETY_FLOOR"    # safety-floor trigger (streak limit / keepalive sampling)
    FAILSAFE = "FAILSAFE"            # fail-safe bypass: dispatch everything (G9)


class Mode(str, Enum):
    """Pipeline run modes (consistent with /service /mode on the control plane)."""

    NORMAL = "NORMAL"
    DEGRADED = "DEGRADED"            # telemetry/audit degraded; data plane keeps filtering
    FAILSAFE_BYPASS = "FAILSAFE_BYPASS"  # dispatch 100% to review


class Reason(str, Enum):
    """Decision reason labels (audit and explainability)."""

    REDUNDANT = "redundant"
    GRAY_PENDING = "gray_pending"
    HYSTERESIS_CONFIRMED = "hysteresis_confirmed"
    GRADUAL_CHANGE = "gradual_change"
    OVERLAY_MUTATION = "overlay_mutation"
    STRONG_QUADRANT_DELTA = "strong_quadrant_delta"
    SCENE_CUT = "scene_cut"
    STREAK_FRAMES = "streak_frames"
    STREAK_SECONDS = "streak_seconds"
    KEEPALIVE = "keepalive"
    FAILSAFE_MODE = "failsafe_mode"
    ADAPTIVE_SCORE = "adaptive_score"


class RegionKind(str, Enum):
    """Overlay/UI region kinds (M3)."""

    CHAT = "chat"
    DANMAKU = "danmaku"
    CAPTION = "caption"
    GAME_UI = "game_ui"


@dataclass(frozen=True)
class Region:
    kind: RegionKind
    x: int
    y: int
    w: int
    h: int
    textiness: float  # 0..1 text-likelihood confidence


@dataclass
class FrameEnvelope:
    """M1 output: normalized frame + metadata. Raw pixel references must never persist across sessions (G2)."""

    stream_id: str
    seq: int
    pts_ns: int                      # source timestamp (estimated when missing)
    t_ingest_ns: int                 # monotonic: normalization complete (latency-budget start)
    width: int
    height: int
    pixel_format: str                # "yuv420p" | "rgb24" | ...
    luma_small: Any = None           # 1/8-pyramid luma (list/ndarray; native buffer)
    pool_ref: Optional[int] = None   # frame-pool slot (zero-copy); never persisted
    trace: dict = field(default_factory=dict)  # stage timestamps {stage: ns}


@dataclass(frozen=True)
class Descriptor:
    """M2 output: non-invertible visual descriptors (G7)."""

    phash64: int
    quad_h: Tuple[int, int, int, int] = (0, 0, 0, 0)   # per-quadrant 16-bit hashes
    overlay_hash: Optional[int] = None                 # filled by M3
    embedding: Optional[Tuple[float, ...]] = None      # gray-zone cascade second-level features (optional)


@dataclass(frozen=True)
class MaskSet:
    """M3 output: region masks + overlay-mutation signal."""

    regions: Tuple[Region, ...] = ()
    overlay_mutation: bool = False
    overlay_score: float = 0.0


@dataclass(frozen=True)
class SimilarityResult:
    """M4 output: differential similarity (all normalized to [0,1]; 0 = identical)."""

    fused: float
    dprev: float
    danchor: float
    mad: float
    quad_q: Tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)
    scene_cut: bool = False

    @property
    def quad_max(self) -> float:
        return max(self.quad_q) if self.quad_q else 0.0


@dataclass
class FrameDecision:
    """M5 output: per-frame decision (external contract; see frame_decision.schema.json)."""

    stream_id: str
    seq: int
    outcome: Outcome
    score: float
    mode: Mode
    config_hash: str
    t_ingest_ns: int
    t_decision_ns: int
    reasons: Tuple[str, ...] = ()
    overlay_mutation: bool = False
    quadrant_max: float = 0.0
    human_review_required: bool = True   # G8: final authority always stays platform-side

    @property
    def latency_ns(self) -> int:
        return self.t_decision_ns - self.t_ingest_ns

    def to_dict(self) -> dict:
        return {
            "stream_id": self.stream_id,
            "seq": self.seq,
            "outcome": self.outcome.value,
            "score": round(self.score, 6),
            "reasons": list(self.reasons),
            "mode": self.mode.value,
            "overlay_mutation": self.overlay_mutation,
            "quadrant_max": round(self.quadrant_max, 6),
            "config_hash": self.config_hash,
            "t_ingest_ns": self.t_ingest_ns,
            "t_decision_ns": self.t_decision_ns,
            "latency_ns": self.latency_ns,
        }
