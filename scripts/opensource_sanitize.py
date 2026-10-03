#!/usr/bin/env python3
"""Open-source sanitization review (deliverable D7): whitelist copy → sensitive-content scan → review report.

Whitelist (planning; finalized in month 6):
  - M1 connectors and normalization, data contracts, benchmark framework (harness / annotations / metrics), M7 audit chain
Scan targets: platform-specific configs, secrets, internal endpoints, sensitive threshold values.
Output: out_dir + sanitize_report.json (per-file hashes).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil

WHITELIST_PREFIXES = (
    "src/streamsieve/modules/m1_normalization",
    "src/streamsieve/common",
    "src/streamsieve/benchmarks",
    "src/streamsieve/modules/m7_telemetry/audit_log.py",
    "configs/schemas",
)

SENSITIVE_PATTERNS = [
    re.compile(r"(?i)(password|secret|token|api[_-]?key)\s*[:=]\s*['\"]"),
    re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"),   # internal-IP hint (manual review; loopback exempt)
    re.compile(r"(?i)internal\.|corp\.|platform-[a-z0-9]+\.example"),
]


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=".")
    ap.add_argument("--out", default="var/opensource")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    report: dict = {"files": [], "warnings": []}
    for root, _dirs, files in os.walk(os.path.join(args.src, "src")):
        for f in files:
            full = os.path.join(root, f)
            rel = os.path.relpath(full, args.src)
            if not rel.startswith(WHITELIST_PREFIXES):
                continue
            try:
                text = open(full, encoding="utf-8").read()
            except (UnicodeDecodeError, OSError):
                continue
            warnings = [p.pattern for p in SENSITIVE_PATTERNS if p.search(text)]
            report["files"].append({"path": rel, "sha256": sha256_file(full), "warnings": warnings})
            if warnings:
                report["warnings"].append({"path": rel, "patterns": warnings})
            if args.apply:
                dest = os.path.join(args.out, rel)
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                shutil.copy2(full, dest)

    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, "sanitize_report.json"), "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    print(f"whitelisted files: {len(report['files'])}; sensitive warnings: {len(report['warnings'])}")
    print(f"report: {os.path.join(args.out, 'sanitize_report.json')}")


if __name__ == "__main__":
    main()
