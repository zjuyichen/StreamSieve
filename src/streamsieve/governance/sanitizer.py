"""G6: timed purge (session temp-directory cleanup; settled within 5 business days after a pilot ends).

Safety design: only paths under the controlled temp root passed in by the caller can be deleted; dry-run by default;
the caller records purge events to the AuditLog (purges must be traceable).
"""
from __future__ import annotations

import os
import shutil
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass
class SanitizeReport:
    root: str
    removed_files: int = 0
    removed_dirs: int = 0
    bytes_freed: int = 0
    dry_run: bool = True

    def to_dict(self) -> dict:
        return {"root": self.root, "removed_files": self.removed_files,
                "removed_dirs": self.removed_dirs, "bytes_freed": self.bytes_freed,
                "dry_run": self.dry_run}


def purge(root: str, *, older_than_hours: float = 24.0, dry_run: bool = True) -> SanitizeReport:
    """Purge aged content under the given temp root. The caller must ensure root is a controlled session directory."""
    rep = SanitizeReport(root=root, dry_run=dry_run)
    root_p = Path(root).resolve()
    if not root_p.exists():
        return rep
    cutoff = time.time() - older_than_hours * 3600
    for path in sorted(root_p.rglob("*"), key=lambda p: len(p.parts), reverse=True):
        try:
            stat = path.stat()
            if stat.st_mtime > cutoff:
                continue
            size = stat.st_size
            if path.is_file():
                rep.removed_files += 1
            elif path.is_dir():
                rep.removed_dirs += 1
            rep.bytes_freed += size
            if not dry_run:
                if path.is_dir():
                    shutil.rmtree(path, ignore_errors=True)
                else:
                    os.unlink(path)
        except FileNotFoundError:
            continue
    return rep


def purge_pilot_end(session_dir: str, *, business_days: int = 5, dry_run: bool = True) -> SanitizeReport:
    """Post-pilot purge (G6): 5 business days ≈ 7 calendar days conservative conversion."""
    hours = business_days * 24.0 * 7.0 / 5.0
    return purge(session_dir, older_than_hours=hours, dry_run=dry_run)
