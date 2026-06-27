"""Bounded queue + backpressure + circuit breaker.

Priority policy (safety first):
1. REVIEW / FORCE_REVIEW / SAFETY_FLOOR / FAILSAFE frames — never dropped silently;
   when full, telemetry capacity is evicted first; if still full → circuit breaker → fail-safe for that stream (full review).
2. telemetry entries — droppable (counted only: sieve_telemetry_dropped_total).

Implementation: an asyncio.Queue wrapper in production; this module provides an asyncio-free counter core for tests.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Priority(str, Enum):
    REVIEW = "review"
    TELEMETRY = "telemetry"


@dataclass
class BoundedQueue:
    capacity: int = 256
    review_depth: int = 0
    telemetry_depth: int = 0
    dropped_telemetry: int = 0
    _breaker_failures: int = 0

    @property
    def depth(self) -> int:
        return self.review_depth + self.telemetry_depth

    def put_review(self) -> bool:
        """Enqueue a review item: consumes capacity; exhaustion → circuit-breaker signal."""
        if self.depth < self.capacity:
            self.review_depth += 1
            return True
        self._breaker_failures += 1
        return False  # caller switches to fail-safe (no frame loss)

    def put_telemetry(self) -> bool:
        if self.depth < self.capacity:
            self.telemetry_depth += 1
            return True
        self.dropped_telemetry += 1
        return False  # telemetry may be dropped (counted only)

    def pop(self, priority: Priority) -> bool:
        if priority == Priority.REVIEW and self.review_depth > 0:
            self.review_depth -= 1
            return True
        if priority == Priority.TELEMETRY and self.telemetry_depth > 0:
            self.telemetry_depth -= 1
            return True
        return False

    @property
    def breaker_tripped(self) -> bool:
        return self._breaker_failures >= 3
