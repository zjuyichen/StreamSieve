"""M1 protocol: stream sources and normalizer."""
from __future__ import annotations

from typing import Iterator, Protocol

from ...common.types import FrameEnvelope


class StreamSource(Protocol):
    """Unified interface for heterogeneous inputs (RTMP/HLS/WebRTC/file/synthetic)."""

    def open(self) -> None: ...
    def frames(self) -> Iterator[FrameEnvelope]: ...   # yields normalized FrameEnvelope objects
    def close(self) -> None: ...
