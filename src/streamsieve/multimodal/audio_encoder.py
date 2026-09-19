"""Audio acoustic encoder (Phase II): open-source self-supervised acoustic model + event classification head; 16 kHz sampling.

Budget ≤ 8 ms per frame group; model provenance and license must be logged in third_party/licenses.md.
"""
from __future__ import annotations


class AudioEncoder:  # pragma: no cover - stub (Phase II)
    def __init__(self, model_path: str = "", sample_rate: int = 16000):
        self.model_path = model_path
        self.sample_rate = sample_rate

    def encode(self, pcm):  # noqa: ANN001
        raise NotImplementedError("audio encoder pending Phase II")
