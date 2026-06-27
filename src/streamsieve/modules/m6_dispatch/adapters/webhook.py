"""Generic REST webhook adapter (external integration surface; TLS 1.3 enforced).

Idempotency: carries the idempotency key stream_id:seq; exponential backoff retries; consecutive failures → circuit breaker (wired to queue.breaker_tripped).
"""
from __future__ import annotations

from dataclasses import dataclass

from ....common.types import FrameDecision


@dataclass
class WebhookAdapter:  # pragma: no cover - stub
    endpoint: str = ""
    tls_min_version: str = "1.3"
    max_attempts: int = 3
    backoff_base_ms: int = 50

    def dispatch(self, decision: FrameDecision, payload_ref: int | None = None) -> bool:
        # TODO(M2-3): implement with requests/httpx + TLS version check + idempotency key
        raise NotImplementedError("Webhook adapter pending (months 2-3)")
