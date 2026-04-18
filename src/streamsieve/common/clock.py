"""Monotonic clock timestamps (µs/ns) — the single measurement entry point for the latency budget."""
from __future__ import annotations

import time


def mono_ns() -> int:
    """Monotonic nanoseconds (independent of wall clock; never reused across restarts)."""
    return time.monotonic_ns()


def stamp(trace: dict, stage: str) -> int:
    """Record a stage timestamp on the frame trace (O(1) hot path; last write wins on key collision)."""
    t = mono_ns()
    trace[stage] = t
    return t
