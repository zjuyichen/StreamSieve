"""Cross-modal attention fusion layer (Phase II, months 7-12).

Interface: takes a sequence of ModalitySignal (visual/audio/text) and outputs a unified risk score (merged into the M5 force-review channel).
All modality tokens are aligned on the time axis; missing modalities are handled by degradation.DegradationPolicy.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ModalitySignal:
    kind: str            # "visual" | "audio" | "text"
    ts_ns: int
    score: float
    reliability: float = 1.0
    features: tuple[float, ...] = ()


class CrossModalFusion:  # pragma: no cover - stub (Phase II)
    def fuse(self, signals: list[ModalitySignal]) -> float:
        # TODO(Phase II): cross-modal attention layer (open-source transformer reference; log the license)
        raise NotImplementedError("cross-modal fusion pending Phase II")
