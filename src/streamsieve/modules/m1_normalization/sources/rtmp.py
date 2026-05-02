"""RTMP source (production sandbox: simulated RTMP ingest endpoints; never connects to unauthorized production streams)."""
from __future__ import annotations

from typing import Iterator

from ....common.types import FrameEnvelope


class RtmpSource:  # pragma: no cover - stub
    def __init__(self, uri: str):
        self.uri = uri

    def open(self) -> None:
        # TODO(M2-3): open via decoder.Decoder(uri)
        raise NotImplementedError

    def frames(self) -> Iterator[FrameEnvelope]:
        raise NotImplementedError

    def close(self) -> None:
        pass
