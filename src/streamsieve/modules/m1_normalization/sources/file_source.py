"""File source (MP4 / pre-recorded clips: single entry point for benchmark datasets and sandbox history)."""
from __future__ import annotations

from typing import Iterator

from ....common.types import FrameEnvelope


class FileSource:  # pragma: no cover - stub
    def __init__(self, path: str, fps_override: float | None = None):
        self.path = path
        self.fps_override = fps_override

    def open(self) -> None:
        raise NotImplementedError

    def frames(self) -> Iterator[FrameEnvelope]:
        raise NotImplementedError

    def close(self) -> None:
        pass
