"""sieve CLI: run | bench | validate-config | sanitize | audit-verify | doctor | version.

Design note: every command maps to a demonstrable capability (used in pilots and audits).
"""
from __future__ import annotations

import argparse
import sys

from ..common.hashing import config_hash
from ..config.loader import load_config
from ..governance import no_train_guard, sanitizer
from ..version import __version__


def cmd_validate_config(args) -> int:
    try:
        cfg = load_config(args.config, args.profile)
    except Exception as exc:  # noqa: BLE001
        print(f"[FAIL] {exc}")
        return 2
    print(f"[OK] config validation passed | config_hash={cfg['_config_hash'][:16]}… | profile={cfg.get('profile')}")
    for key in ("decision", "failsafe", "governance"):
        if key in cfg:
            print(f"  - {key}: loaded")
    return 0


def cmd_doctor(args) -> int:
    problems = []
    import shutil as _shutil

    if _shutil.which("ffmpeg") is None:
        problems.append("ffmpeg not on PATH (needed by M1 production decoding; wired in months 2-3)")
    try:
        import yaml as _yaml  # noqa: F401,PLC0415
    except ImportError:
        if _shutil.which("ruby") is None:
            problems.append("no YAML parser available: pip install pyyaml")
    hits = no_train_guard.scan_source("src/streamsieve")
    if hits:
        problems.append(f"{len(hits)} suspected training-code pattern(s) found (G4)")
    if problems:
        print("[WARN] environment diagnostics:")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("[OK] environment check passed")
    return 0


def cmd_audit_verify(args) -> int:
    import os

    from ..modules.m7_telemetry.audit_log import AuditLog

    key = os.environ.get("SIEVE_AUDIT_KEY", "dev-key").encode()
    log = AuditLog(path=args.path, key=key)
    ok, n = log.verify()
    print(f"[{'OK' if ok else 'FAIL'}] audit chain: {n} records, intact={ok}")
    return 0 if ok else 3


def cmd_sanitize(args) -> int:
    rep = sanitizer.purge(args.root, older_than_hours=args.older_hours, dry_run=not args.apply)
    print(f"[{'APPLY' if args.apply else 'DRY-RUN'}] purge {rep.root}: "
          f"files={rep.removed_files} dirs={rep.removed_dirs} bytes={rep.bytes_freed}")
    return 0


def cmd_run(args) -> int:
    print("run: skeleton — the engine data plane lands in months 2-3. For now, use `make demo` for the reference implementation.")
    cfg = load_config(args.config, args.profile)
    print(f"config hash: {cfg['_config_hash'][:16]}…")
    return 0


def cmd_bench(args) -> int:
    print("bench: skeleton — benchmarks.harness lands in months 2-3; synthetic scenarios can be validated with the reference implementation today.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="sieve", description="StreamSieve command line")
    p.add_argument("--version", action="version", version=f"streamsieve {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    sp = sub.add_parser("run", help="run the pipeline")
    sp.add_argument("--config", default="configs/default.yaml")
    sp.add_argument("--profile", default=None)
    sp.set_defaults(fn=cmd_run)

    sp = sub.add_parser("bench", help="matched-baseline benchmark")
    sp.add_argument("--config", default="configs/default.yaml")
    sp.add_argument("--profile", default=None)
    sp.set_defaults(fn=cmd_bench)

    sp = sub.add_parser("validate-config", help="validate configuration")
    sp.add_argument("--config", default="configs/default.yaml")
    sp.add_argument("--profile", default=None)
    sp.set_defaults(fn=cmd_validate_config)

    sp = sub.add_parser("sanitize", help="purge session/temp directories (G6)")
    sp.add_argument("root")
    sp.add_argument("--older-hours", type=float, default=24.0)
    sp.add_argument("--apply", action="store_true", help="actually delete (default: dry-run)")
    sp.set_defaults(fn=cmd_sanitize)

    sp = sub.add_parser("audit-verify", help="verify audit-chain integrity")
    sp.add_argument("path")
    sp.set_defaults(fn=cmd_audit_verify)

    sp = sub.add_parser("doctor", help="environment diagnostics")
    sp.set_defaults(fn=cmd_doctor)

    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
