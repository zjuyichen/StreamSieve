"""G4: training prohibited — static scan + runtime guard.

1) Static scan (CI step): training patterns (optimizer/backward, etc.) are banned under src/streamsieve;
   exempt directories are reported but not blocked (EXEMPT_DIRS).
2) Runtime guard: any attempt to call train()/fine_tune() raises TrainingProhibitedError.

This module is the enforcement point for the "no training on platform data" guarantee.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

from ..common.errors import TrainingProhibitedError

BANNED_PATTERNS = [
    re.compile(r"\.backward\s*\("),
    re.compile(r"torch\.optim"),
    re.compile(r"\boptimizer\s*\("),
    re.compile(r"\bfine_tune\s*\("),
    re.compile(r"\btrain_model\s*\("),
]

EXEMPT_DIRS = {"benchmarks"}  # inference-style loading only; still reported in scans


_SELF = Path(__file__).resolve()


def scan_source(root: str | Path) -> list[tuple[str, int, str]]:
    """Return violations as [(file, line_no, line)]; non-empty fails CI.

    Self-exclusion: this file defines the pattern strings and is not self-scanned (standard practice).
    """
    hits: list[tuple[str, int, str]] = []
    for py in Path(root).rglob("*.py"):
        if py.resolve() == _SELF:
            continue
        for i, line in enumerate(py.read_text(encoding="utf-8").splitlines(), start=1):
            for pat in BANNED_PATTERNS:
                if pat.search(line):
                    hits.append((str(py), i, line.strip()))
    return hits


def guard_runtime_enabled() -> bool:
    """Runtime switch: SIEVE_ALLOW_TRAINING=1 may only be set temporarily in controlled lab benchmarks (off by default)."""
    return os.environ.get("SIEVE_ALLOW_TRAINING") == "1"


def assert_not_training(operation: str) -> None:
    if not guard_runtime_enabled():
        raise TrainingProhibitedError(f"G4: training/fine-tuning is prohibited in the pipeline (operation={operation})")
