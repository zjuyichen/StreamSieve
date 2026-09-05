"""Matched-baseline runner (NIST-aligned; DESIGN §9.1).

Flow:
  for scenario in scenarios:
      control  = run(mode="control")    # all frames reviewed (inference stand-in)
      filtered = run(mode="filtered")   # this pipeline + the same stand-in
      summary  = compare(control, filtered)
  emit reports/<run_id>/...

Status: to be wired in months 2-3 (the reference implementation can already run the synthetic filtered path).
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Scenario:
    name: str
    source: str                    # file / synthetic stream identifier
    annotations_path: str | None = None
    fps: float = 60.0


@dataclass
class RunConfig:
    scenarios: list[Scenario] = field(default_factory=list)
    config_path: str = "configs/default.yaml"
    profile_path: str | None = None
    run_id: str = ""


def run_benchmark(run: RunConfig) -> str:  # pragma: no cover - stub
    """Run all scenarios and return the reports/<run_id>/ path."""
    raise NotImplementedError("benchmark runner pending (months 2-3; the reference path already works for synthetic scenarios)")
