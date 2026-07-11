"""Audit log: HMAC hash chain (append-only, whole-chain verifiable) — implementation of G10.

Format (JSONL, one record per line):
  {"seq": n, "ts_ns": ..., "event": "...", "payload": {...},
   "prev_hmac": "...", "hmac": "..."}
where hmac = HMAC-SHA256(key, canonical(seq, ts_ns, event, payload, prev_hmac)).

Write-failure policy: raise AuditWriteError → the caller degrades to DEGRADED + alert (never silent).
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any

from ...common.errors import StreamSieveError
from ...common.hashing import hmac_hex


class AuditWriteError(StreamSieveError):
    """Audit write failed (the data plane must degrade and alert)."""


@dataclass
class AuditLog:
    path: str
    key: bytes
    _seq: int = 0
    _prev_hmac: str = ""
    _fh: Any = field(default=None, repr=False)

    def open(self) -> None:
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        self._fh = open(self.path, "a", encoding="utf-8")  # noqa: SIM115
        # restore chain tail (supports resuming after a process restart)
        self._seq, self._prev_hmac = self._tail_state()

    def _tail_state(self) -> tuple[int, str]:
        seq, prev = 0, ""
        if os.path.exists(self.path):
            with open(self.path, "r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    rec = json.loads(line)
                    seq, prev = rec.get("seq", seq), rec.get("hmac", prev)
        return seq, prev

    def append(self, event: str, payload: dict) -> dict:
        self._seq += 1
        ts = time.time_ns()
        body = {"seq": self._seq, "ts_ns": ts, "event": event, "payload": payload,
                "prev_hmac": self._prev_hmac}
        message = json.dumps(body, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
        digest = hmac_hex(self.key, message)
        rec = {**body, "hmac": digest}
        try:
            if self._fh is None:
                raise AuditWriteError("audit log not open (call open() first)")
            self._fh.write(json.dumps(rec, sort_keys=True, default=str) + "\n")
            self._fh.flush()
            os.fsync(self._fh.fileno())
        except OSError as exc:
            raise AuditWriteError(f"audit write failed: {exc}") from exc
        self._prev_hmac = digest
        return rec

    def verify(self) -> tuple[bool, int]:
        """Verify the whole chain: returns (intact, record_count)."""
        prev = ""
        count = 0
        with open(self.path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                body = {k: rec[k] for k in ("seq", "ts_ns", "event", "payload", "prev_hmac")}
                if body["prev_hmac"] != prev:
                    return False, count
                message = json.dumps(body, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
                if hmac_hex(self.key, message) != rec["hmac"]:
                    return False, count
                prev = rec["hmac"]
                count += 1
        return True, count

    def close(self) -> None:
        if self._fh is not None:
            self._fh.close()
            self._fh = None
