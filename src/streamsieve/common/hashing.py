"""Hashing and signing utilities: xxhash-style content hash (stdlib fallback), HMAC chain, config_hash."""
from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def config_hash(config: dict) -> str:
    """Reproducibility anchor: sha256 of the canonical JSON."""
    canonical = json.dumps(config, sort_keys=True, separators=(",", ":"), default=str)
    return sha256_hex(canonical.encode("utf-8"))


def hmac_hex(key: bytes, message: bytes) -> str:
    return hmac.new(key, message, hashlib.sha256).hexdigest()


def content_hash(obj: Any) -> int:
    """Content hash (used for overlay-region fingerprints; production uses xxhash64, stdlib fallback here)."""
    payload = json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)
    return int.from_bytes(hashlib.blake2b(payload.encode("utf-8"), digest_size=8).digest(), "big")
