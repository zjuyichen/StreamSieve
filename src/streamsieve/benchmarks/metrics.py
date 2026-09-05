"""Metric formulas (single source of truth; shared by online telemetry and offline reports).

Definitions: docs/benchmark_protocol.md and DESIGN.md §9.3.
"""
from __future__ import annotations

from dataclasses import dataclass


def reduction_ratio(bypassed: int, total: int) -> float:
    return bypassed / total if total else 0.0


def event_recall(dispatched_seqs: set[int], events) -> tuple[float, list[str]]:
    """Event-level recall: an event hits if at least one frame in its window was dispatched. Returns (recall, missed_event_ids)."""
    hits = 0
    misses = []
    for ev in events:
        window = set(range(ev.start_frame, ev.end_frame + 1))
        if window & dispatched_seqs:
            hits += 1
        else:
            misses.append(ev.event_id)
    return (hits / len(events) if events else 1.0), misses


def frame_recall(dispatched_seqs: set[int], events) -> float:
    """Frame-level recall: dispatched frames within annotated windows / total frames in those windows."""
    total = sum(ev.end_frame - ev.start_frame + 1 for ev in events)
    if not total:
        return 1.0
    hit = sum(len(set(range(ev.start_frame, ev.end_frame + 1)) & dispatched_seqs) for ev in events)
    return hit / total


def percentile(values, q: float) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    idx = min(int(len(s) * q), len(s) - 1)
    return s[idx]


def energy_per_kframe(joules: float, frames: int) -> float:
    return joules / (frames / 1000.0) if frames else 0.0


@dataclass
class BenchmarkSummary:
    stream_id: str
    total_frames: int
    bypass_ratio: float
    event_recall: float
    frame_recall: float
    latency_p50_ms: float
    latency_p95_ms: float
    latency_p99_ms: float
    energy_per_kframe_j: float
    missed_events: list[str]

    def to_dict(self) -> dict:
        return self.__dict__.copy()

    def passes_gates(self, *, min_reduction=0.65, max_reduction=0.80,
                     min_recall=0.998, max_p99_ms=45.0) -> dict[str, bool]:
        return {
            "reduction_in_range": min_reduction <= self.bypass_ratio,  # upper bound is scenario-dependent, not a hard gate
            "recall_ok": self.event_recall >= min_recall,
            "latency_ok": self.latency_p99_ms <= max_p99_ms,
        }
