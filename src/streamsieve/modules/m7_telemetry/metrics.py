"""Prometheus metric registry (single naming convention `sieve_*`).

Design principles:
- the hot path only does O(1) in-memory counting; silently degrades to built-in counters without prometheus_client;
- the metric set maps 1:1 to DESIGN.md §5 (M7); never invent names elsewhere.
"""
from __future__ import annotations

from dataclasses import dataclass, field

try:  # optional dependency
    from prometheus_client import Counter, Gauge, Histogram  # noqa: F401
    _PROM = True
except ImportError:  # pragma: no cover
    _PROM = False

METRIC_FRAMES = "sieve_frames_total"                  # labels: stream,outcome
METRIC_BYPASS_RATIO = "sieve_bypass_ratio"            # labels: stream
METRIC_STAGE_LATENCY = "sieve_stage_latency_seconds"  # labels: stage
METRIC_QUEUE_DEPTH = "sieve_queue_depth"              # labels: stage
METRIC_ENERGY = "sieve_energy_joules_total"           # labels: device
METRIC_FAILSAFE = "sieve_failsafe_activations_total"
METRIC_RECALL_PROBE = "sieve_recall_probe_total"
METRIC_AUDIT_FAILURES = "sieve_audit_write_failures_total"
METRIC_TELEMETRY_DROPPED = "sieve_telemetry_dropped_total"
METRIC_FRAMES_DROPPED = "sieve_frames_dropped_total"   # soak gate: must stay at 0


@dataclass
class InMemoryMetrics:
    """Built-in counters for environments without Prometheus (tests/local)."""

    frames_by_outcome: dict[str, int] = field(default_factory=dict)
    stage_latency_ns_sum: dict[str, int] = field(default_factory=dict)
    stage_latency_ns_count: dict[str, int] = field(default_factory=dict)
    failsafe_activations: int = 0
    audit_write_failures: int = 0
    telemetry_dropped: int = 0

    def frame(self, outcome: str) -> None:
        self.frames_by_outcome[outcome] = self.frames_by_outcome.get(outcome, 0) + 1

    def latency(self, stage: str, ns: int) -> None:
        self.stage_latency_ns_sum[stage] = self.stage_latency_ns_sum.get(stage, 0) + ns
        self.stage_latency_ns_count[stage] = self.stage_latency_ns_count.get(stage, 0) + 1

    @property
    def bypass_ratio(self) -> float:
        total = sum(self.frames_by_outcome.values())
        return self.frames_by_outcome.get("BYPASS", 0) / total if total else 0.0
