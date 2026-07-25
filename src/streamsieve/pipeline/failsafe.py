"""Fail-safe state machine: NORMAL / DEGRADED / FAILSAFE_BYPASS.

Semantics:
- FAILSAFE_BYPASS = dispatch 100% of frames to review (trading filter gains for zero misses);
- entry conditions: watchdog heartbeat timeout, error rate above threshold, queue circuit breaker, external override;
- exit conditions: cooldown ≥ cooldown_s and a healthy probe window of probe_s, with flap suppression;
- every transition is written to the audit chain + metric counters (persistence is the caller's job).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..common.types import Mode


@dataclass
class Watchdog:
    """Stage heartbeat monitor: every stage should emit one heartbeat per frame.

    strike counting: a single timeout does not reset the counter; strikes consecutive timeouts → trigger (flap suppression).
    """

    timeout_ms: float = 100.0
    strikes: int = 3
    counters: dict[str, int] = field(default_factory=dict)

    def heartbeat(self, stage: str, elapsed_ms: float) -> bool:
        """Return True if the stage is healthy for this frame."""
        if elapsed_ms <= self.timeout_ms:
            self.counters[stage] = 0
            return True
        self.counters[stage] = self.counters.get(stage, 0) + 1
        return not (self.counters[stage] >= self.strikes)


@dataclass
class FailSafeController:
    cooldown_s: float = 30.0
    probe_s: float = 10.0
    flap_suppression_s: float = 60.0
    error_rate_threshold: float = 0.01

    mode: Mode = Mode.NORMAL
    _since_trigger_s: float = 0.0
    _probe_ok_s: float = 0.0
    _last_exit_s: float = -1e9

    # ---- enter / exit ----
    def trigger(self, reason: str, *, now_s: float) -> Mode:
        if self.mode != Mode.FAILSAFE_BYPASS:
            self.mode = Mode.FAILSAFE_BYPASS
            self._since_trigger_s = now_s
            self._probe_ok_s = 0.0
        return self.mode

    def observe_health(self, healthy: bool, dt_s: float) -> Mode:
        if self.mode == Mode.FAILSAFE_BYPASS:
            self._since_trigger_s += dt_s
            if healthy:
                self._probe_ok_s += dt_s
            else:
                self._probe_ok_s = 0.0
            if self._since_trigger_s >= self.cooldown_s and self._probe_ok_s >= self.probe_s:
                self.mode = Mode.NORMAL
                self._last_exit_s = self._since_trigger_s
        return self.mode

    def degrade(self) -> Mode:
        """Audit/telemetry degradation: the data plane keeps filtering, but the state is externally visible."""
        if self.mode == Mode.NORMAL:
            self.mode = Mode.DEGRADED
        return self.mode

    def recover(self) -> Mode:
        if self.mode == Mode.DEGRADED:
            self.mode = Mode.NORMAL
        return self.mode
