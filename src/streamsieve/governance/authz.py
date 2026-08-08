"""G5: least privilege (scope allowlist + MFA flag)."""
from __future__ import annotations

from dataclasses import dataclass, field

from ..common.errors import GovernanceError

ALLOWED_SCOPES = {"sandbox.read", "sandbox.write"}


@dataclass
class AccessPolicy:
    require_mfa: bool = True
    granted: set[str] = field(default_factory=set)

    def grant(self, token_scopes: list[str], mfa: bool) -> None:
        if self.require_mfa and not mfa:
            raise GovernanceError("G5 violation: MFA missing")
        for s in token_scopes:
            if s not in ALLOWED_SCOPES:
                raise GovernanceError(f"G5 violation: scope outside the sandbox allowlist: {s}")
        self.granted = set(token_scopes)

    def require(self, scope: str) -> None:
        if scope not in self.granted:
            raise GovernanceError(f"permission denied: {scope} required")
