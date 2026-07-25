"""Orchestration engine: declarative per-stream pipeline assembly.

Structure (data-plane wiring lands in months 2-3; a testable scheduling skeleton is provided now):

  source → [M1] → [M2] → [M3] → [M4] → [M5] ─┬─► BYPASS (count + cache reference)
                                              └─► [M6] → platform / human review
  M7 subscribes to per-frame decisions and stage timings (never blocks the main path)

Micro-batch strategy (latency first):
- enable micro-batches up to micro_batch_max for M2/M4 only when the per-stream queue depth ≥ micro_batch_queue_trigger;
- if the end-to-end p99 histogram ever breaches budget → watchdog alerts and disables micro-batching (degradation path).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..common.types import FrameDecision, Mode
from .failsafe import FailSafeController, Watchdog


@dataclass
class StreamRuntime:
    """Per-stream runtime state (with DecisionState, the full set of mutable per-stream state)."""

    stream_id: str
    mode: Mode = Mode.NORMAL
    metrics: Any = None                     # InMemoryMetrics / Prometheus wrapper
    watchdog: Watchdog = field(default_factory=Watchdog)
    failsafe: FailSafeController = field(default_factory=FailSafeController)
    stages: list[Any] = field(default_factory=list)   # StageSpec list (populated at assembly time)

    def route(self, decision: FrameDecision) -> str:
        """Map a decision to a routing action (used by the dispatcher / counters)."""
        return "failsafe" if decision.outcome.value == "FAILSAFE" else (
            "bypass" if decision.outcome.value == "BYPASS" else "review"
        )


class Engine:
    """Assembly and execution skeleton. The data-plane implementation (asyncio task graph) lands in months 2-3.

    schedule_decision() implements the pure scheduling logic (unit-testable):
    - micro-batch toggle checks;
    - fail-safe mode mapping;
    - stage heartbeats fed to the watchdog.
    """

    def __init__(self, config: dict):
        self.config = config
        self.runtimes: dict[str, StreamRuntime] = {}
        self._micro_batch_enabled = True

    def register_stream(self, stream_id: str, metrics: Any) -> StreamRuntime:
        rt = StreamRuntime(stream_id=stream_id, metrics=metrics)
        self.runtimes[stream_id] = rt
        return rt

    def should_micro_batch(self, queue_depth: int) -> bool:
        if not self._micro_batch_enabled:
            return False
        trigger = self.config.get("pipeline", {}).get("micro_batch_queue_trigger", 8)
        return queue_depth >= trigger

    def on_latency_breach(self) -> None:
        """p99 breach: disable micro-batching first (cheapest degradation)."""
        self._micro_batch_enabled = False
        for rt in self.runtimes.values():
            rt.failsafe.degrade()

    def stage_heartbeat(self, stream_id: str, stage: str, elapsed_ms: float) -> bool:
        rt = self.runtimes[stream_id]
        ok = rt.watchdog.heartbeat(stage, elapsed_ms)
        if not ok:
            rt.failsafe.trigger(f"stage_timeout:{stage}", now_s=0.0)
            rt.mode = rt.failsafe.mode
        return ok
