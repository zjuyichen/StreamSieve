"""HLS source (sandbox: pre-recorded or synthetic HLS playlists)."""
from __future__ import annotations

from typing import Iterator

from ....common.types import FrameEnvelope


class HlsSource:  # pragma: no cover - stub
    def __init__(self, uri: str):
        self.uri = uri

    def open(self) -> None:
        raise NotImplementedError

    def frames(self) -> Iterator[FrameEnvelope]:
        raise NotImplementedError

    def close(self) -> None:
        pass
