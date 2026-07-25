"""Stage abstraction: backpressure-aware, timestamped, timeout-bounded.

Conventions:
- each stage is an async callable: process(item) -> item | None;
- timing is injected centrally by the runner (no scattered timing code inside stages);
- timeouts (latency.stage_gates_ms) are monitored by the engine watchdog; stages never swallow exceptions.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Protocol


class AsyncStage(Protocol):
    name: str

    def __call__(self, item: Any) -> Awaitable[Any]: ...


@dataclass
class StageSpec:
    name: str          # "m1" | ... | "m6"
    fn: Callable[[Any], Awaitable[Any]]
    gate_ms: float     # from config.latency.stage_gates_ms
