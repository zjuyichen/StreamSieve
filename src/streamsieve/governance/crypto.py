"""G3: encryption constraints (TLS 1.3 / AES-256-GCM)."""
from __future__ import annotations

from dataclasses import dataclass

from ..common.errors import GovernanceError

MIN_TLS = "1.3"


@dataclass(frozen=True)
class TransportPolicy:
    tls_min_version: str = MIN_TLS
    cipher: str = "AES-256-GCM"
    sandbox_loopback_allowed: bool = True

    def check(self, url: str, tls_version: str | None = None) -> None:
        """Validate that the target endpoint satisfies the transport policy (non-sandbox environments require https + TLS 1.3)."""
        if url.startswith("https://"):
            if tls_version is not None and tls_version < self.tls_min_version:
                raise GovernanceError(f"G3 violation: TLS {tls_version} < {self.tls_min_version}")
            return
        if url.startswith("http://"):
            if self.sandbox_loopback_allowed and ("127.0.0.1" in url or "localhost" in url):
                return  # loopback plaintext allowed for the local sandbox mock queue
            raise GovernanceError("G3 violation: non-sandbox endpoints must use TLS 1.3")
