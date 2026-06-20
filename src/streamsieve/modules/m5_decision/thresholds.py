"""Multi-tier thresholds + adaptive factor (EWMA, clamped to [0.5, 2.0]).

Only t_bypass is adapted (how lenient "redundant" is); these are NEVER touched:
- t_force (force-review threshold)
- scene-cut threshold
- overlay-mutation test
- safety floors (streak caps / keepalive)
This keeps adaptation on the benefit side only, never on the safety side (design invariant INV3).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AdaptiveThreshold:
    alpha: float = 0.05
    clamp_lo: float = 0.5
    clamp_hi: float = 2.0
    enabled: bool = True

    ewma_score: float = 0.0
    factor: float = 1.0
    _initialized: bool = False

    def update(self, score: float) -> None:
        if not self._initialized:
            self.ewma_score = score
            self._initialized = True
        else:
            self.ewma_score = (1 - self.alpha) * self.ewma_score + self.alpha * score
        if not self.enabled:
            self.factor = 1.0
            return
        # more dynamic content (higher mean delta) → less leniency allowed (factor shrinks toward clamp_lo)
        # conversely, static streams allow a looser bypass threshold, raising the reduction ratio.
        target = 1.0 + (0.02 - min(self.ewma_score, 0.10)) * 5.0
        self.factor = max(self.clamp_lo, min(self.clamp_hi, target))
