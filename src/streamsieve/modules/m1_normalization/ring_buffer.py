"""M1 frame pool / ring buffer: zero-copy refcounting; zeroed on release; never persisted (G2).

Mechanism:
- preallocate N slots (capacity = queue depth + in-flight upper bound);
- FrameEnvelope.pool_ref points at a slot; release zero-fills the slot (no residual data);
- any attempt to write slot contents to disk is rejected in governance.retention.
"""
from __future__ import annotations

from typing import Any


class FramePool:  # pragma: no cover - stub
    def __init__(self, slots: int, frame_bytes: int):
        self.slots = slots
        self.frame_bytes = frame_bytes
        self._pool: list[Any] = [None] * slots
        self._in_use: set[int] = set()

    def acquire(self):
        for i, slot in enumerate(self._pool):
            if i not in self._in_use:
                self._in_use.add(i)
                return i, slot
        raise BufferError("frame pool exhausted (backpressure should have kicked in earlier)")

    def release(self, idx: int, zero: bool = True) -> None:
        # TODO(M2-3): overwrite the buffer when zero=True
        self._in_use.discard(idx)

    @property
    def utilization(self) -> float:
        return len(self._in_use) / self.slots
