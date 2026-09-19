"""Text encoder (Phase II): streaming NLP encoder for chat/danmaku text (lightweight transformer, window-aggregated).

Input is limited to authorized sandbox text (G1/G4); output vectors must not contain reversible text information (G7 spirit).
"""
from __future__ import annotations


class TextEncoder:  # pragma: no cover - stub (Phase II)
    def __init__(self, model_path: str = ""):
        self.model_path = model_path

    def encode(self, texts: list[str]) -> tuple[float, ...]:
        raise NotImplementedError("text encoder pending Phase II")
