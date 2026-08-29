"""Health and mode endpoints: /healthz /readyz /mode (K8s probes and operations)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class HealthState:
    alive: bool = True
    ready: bool = False          # ready only after the first stream registers and config validation passes
    mode: str = "NORMAL"         # NORMAL | DEGRADED | FAILSAFE_BYPASS
    failsafe_activations: int = 0

    def snapshot(self) -> dict:
        return {"alive": self.alive, "ready": self.ready, "mode": self.mode,
                "failsafe_activations": self.failsafe_activations}
