"""Energy sampling: GPU = NVML, CPU = RAPL; falls back to a power-model estimate (flagged) when unavailable.

Everything is reported in joules (J). Audit reports must carry raw samples and the estimate flag (reviewable methodology; DESIGN §9.3).
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable


@dataclass
class EnergySampler:
    """Sampler with injectable readers (easy to test and swap).

    - gpu_reader: () -> watts   (NVML nvmlDeviceGetPowerUsage/1000)
    - cpu_reader: () -> watts   (RAPL differential)
    - estimator: prefer real readings; otherwise fall back to the estimator
    """

    gpu_reader: Callable[[], float] | None = None
    cpu_reader: Callable[[], float] | None = None
    estimator: Callable[[], float] | None = None
    sample_interval_s: float = 0.1

    gpu_joules: float = 0.0
    cpu_joules: float = 0.0
    estimated: bool = False
    _last_t: float = field(default_factory=lambda: 0.0)

    def sample(self) -> None:
        now = time.monotonic()
        if self._last_t == 0.0:
            self._last_t = now
            return
        dt = now - self._last_t
        self._last_t = now
        if self.gpu_reader is not None:
            try:
                self.gpu_joules += max(self.gpu_reader(), 0.0) * dt
            except Exception:  # noqa: BLE001
                self.estimated = True
        elif self.estimator is not None:
            self.gpu_joules += max(self.estimator(), 0.0) * dt
            self.estimated = True
        if self.cpu_reader is not None:
            try:
                self.cpu_joules += max(self.cpu_reader(), 0.0) * dt
            except Exception:  # noqa: BLE001
                self.estimated = True

    @property
    def total_joules(self) -> float:
        return self.gpu_joules + self.cpu_joules
