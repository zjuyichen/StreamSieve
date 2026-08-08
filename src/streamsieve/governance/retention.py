"""G2/G6: zero-retention policy enforcement.

Mechanism:
- persist_raw_frames is always false (enforced by config.loader guardrails);
- can_persist() rejects any attempt to persist raw pixels;
- session temp-directory TTL is enforced by the sanitizer.
"""
from __future__ import annotations

from ..common.errors import GovernanceError

_ALLOWED_PERSISTABLE = {"hashes", "embeddings", "decisions", "metrics", "annotations"}


def can_persist(kind: str) -> bool:
    """Whether a data kind may be persisted. Raw frames/pixels ('raw') are never allowed (G2)."""
    return kind in _ALLOWED_PERSISTABLE


def assert_persistable(kind: str) -> None:
    if not can_persist(kind):
        raise GovernanceError(f"G2 violation: persisting {kind!r} is forbidden (zero raw-frame retention)")
