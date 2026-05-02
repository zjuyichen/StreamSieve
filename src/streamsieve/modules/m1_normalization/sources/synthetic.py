"""Synthetic source: standard month-1 sandbox fixture (end-to-end validation with no dataset).

Patterns (see scripts/gen_synthetic_stream.py):
- static gradient (validates high reduction ratio)
- scrolling bar / moving square (validates hysteresis and the gray zone)
- overlay text-block mutation (validates the M3 → force-review channel)
- scene cut (validates anchor refresh)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterator

from ....common.types import FrameEnvelope


@dataclass
class SyntheticPattern:
    name: str
    luma_fn: Callable[[int, int, int], list[list[float]]]  # (frame_idx, h, w) -> luma


class SyntheticSource:
    """Pure in-memory synthetic source (no third-party deps); consumed directly by the reference implementation and tests."""

    def __init__(self, pattern: SyntheticPattern, frames: int, stream_id: str = "synthetic", fps: float = 60.0):
        self.pattern = pattern
        self.n_frames = frames
        self.stream_id = stream_id
        self.fps = fps

    def open(self) -> None:
        pass

    def frames(self) -> Iterator[FrameEnvelope]:
        import time as _time

        for i in range(self.n_frames):
            h = w = 32
            luma = self.pattern.luma_fn(i, h, w)
            yield FrameEnvelope(
                stream_id=self.stream_id,
                seq=i,
                pts_ns=int(i * 1e9 / self.fps),
                t_ingest_ns=_time.monotonic_ns(),
                width=w,
                height=h,
                pixel_format="luma32",
                luma_small=luma,
            )

    def close(self) -> None:
        pass
