"""M1 decoder: PyAV/FFmpeg → normalized tensors + 1/8 luma pyramid.

Production notes (filled in months 2-3):
- PyAV opens RTMP/HLS/WebRTC/MP4; NVDEC on cloud, VideoToolbox on local Macs;
- unified color space: YUV420p; derive the 1/8-resolution luma pyramid (the single source for downstream modules);
- `t_ingest_ns` is stamped the moment normalization completes (latency-budget start);
- decode errors counted in a sliding window → FailSafeError above threshold.
"""
from __future__ import annotations

from ...common.errors import FailSafeError


class Decoder:  # pragma: no cover - stub
    """Placeholder: the real implementation depends on av/numpy (extras: video)."""

    def __init__(self, uri: str, *, nvdec: bool = False, error_rate_threshold: float = 0.01):
        self.uri = uri
        self.nvdec = nvdec
        self.error_rate_threshold = error_rate_threshold

    def open(self) -> None:
        try:
            import av  # noqa: F401,PLC0415
        except ImportError as exc:
            raise FailSafeError("av dependency missing (pip install 'streamsieve[video]')") from exc
        # TODO(M2-3): open container/decoder, configure thread pool and hardware acceleration
        raise NotImplementedError("Decoder production implementation pending (months 2-3)")

    def normalize(self, av_frame) -> None:
        # TODO(M2-3): → FrameEnvelope(yuv420p, luma_small=1/8 pyramid)
        raise NotImplementedError
