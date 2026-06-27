"""Mock enterprise review-queue adapter (standard sandbox fixture).

Semantics: HTTP POST of decision records to a local mock endpoint (e.g., http://127.0.0.1:8081/ingest),
validating dispatch, retry, and idempotency without any platform production system.
TLS: plain http by default in the sandbox; the pilot_sandbox profile enforces TLS 1.3 (G3).
"""
from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass

from ....common.types import FrameDecision


@dataclass
class MockQueueAdapter:
    endpoint: str = "http://127.0.0.1:8081/ingest"
    timeout_ms: int = 200
    max_attempts: int = 3

    def dispatch(self, decision: FrameDecision, payload_ref: int | None = None) -> bool:  # pragma: no cover - network stub
        body = json.dumps(decision.to_dict()).encode("utf-8")
        for _ in range(self.max_attempts):
            try:
                req = urllib.request.Request(
                    self.endpoint, data=body, headers={"Content-Type": "application/json"}, method="POST"
                )
                with urllib.request.urlopen(req, timeout=self.timeout_ms / 1000.0) as resp:  # noqa: S310
                    return 200 <= resp.status < 300
            except Exception:  # noqa: BLE001
                continue
        return False
