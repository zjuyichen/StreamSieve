"""Change-event annotation format (ground truth) and loading.

Format (docs/benchmark_protocol.md §4):
  {"stream_id": ..., "fps": 60, "events": [
     {"event_id": "e1", "type": "risk_delta|overlay_mutation|scene_change|static",
      "start_frame": 120, "end_frame": 135, "quadrants": ["q2"],
      "label": "...", "severity": "high"}]}
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field


@dataclass
class Event:
    event_id: str
    type: str
    start_frame: int
    end_frame: int
    label: str = ""
    severity: str = "medium"
    quadrants: list[str] = field(default_factory=list)


@dataclass
class AnnotationSet:
    stream_id: str
    fps: float
    events: list[Event]

    @property
    def n_events(self) -> int:
        return len(self.events)


def load(path: str) -> AnnotationSet:
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    events = [Event(**e) for e in data.get("events", [])]
    return AnnotationSet(stream_id=data["stream_id"], fps=data.get("fps", 60.0), events=events)
