"""M2 second-level features: ONNX lightweight embedding (gray-zone cascade; open-licensed models, registry-logged).

Production notes:
- onnxruntime (CPU/GPU) lazy-loaded; model path from config, verified against sha256 and the license registry;
- timeout (config.features.embedding.timeout_ms) → drop the embedding and keep the first-level hash (degrade, don't fail).
"""
from __future__ import annotations


class OnnxEmbedder:  # pragma: no cover - stub, filled in months 2-3
    """Placeholder: returns None when disabled/load-failed; callers degrade automatically."""

    def __init__(self, model_path: str, timeout_ms: int = 3, providers: list[str] | None = None):
        self.model_path = model_path
        self.timeout_ms = timeout_ms
        self.providers = providers or ["CPUExecutionProvider"]
        self._session = None

    def load(self) -> bool:
        # TODO(M2-3): onnxruntime.InferenceSession(model_path, providers=self.providers)
        return False

    def infer(self, luma_small) -> tuple[float, ...] | None:
        # TODO(M2-3): preprocess → session.run → L2-normalized vector
        return None
