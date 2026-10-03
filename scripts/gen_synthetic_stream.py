#!/usr/bin/env python3
"""Generate synthetic video streams (PGM sequence + manifest.json) as sandbox/test/stress fixtures.

Pure stdlib (no ffmpeg / third-party required); production stress runs can use ffmpeg-encoded streams instead.
Usage: PYTHONPATH=src python3 scripts/gen_synthetic_stream.py --out var/synthetic --frames 300
"""
from __future__ import annotations

import argparse
import json
import os


def pattern_static(i: int) -> list[list[int]]:
    """Static gradient (validates a high reduction ratio)."""
    return [[(x * 3 + y * 2 + 40) % 256 for x in range(64)] for y in range(64)]


def pattern_motion(i: int) -> list[list[int]]:
    """Moving square (validates the gray zone / hysteresis)."""
    base = [[60 for _ in range(64)] for _ in range(64)]
    x0, y0 = (i * 2) % 48, 20
    for y in range(y0, y0 + 12):
        for x in range(x0, x0 + 12):
            base[y][x] = 220
    return base


def pattern_overlay(i: int) -> list[list[int]]:
    """Scrolling text strip at the bottom (validates overlay-mutation force review)."""
    base = pattern_static(i)
    if i >= 20:
        phase = (i - 20) % 8
        for y in range(52, 60):
            for x in range(0, 64):
                base[y][x] = 255 if ((x + phase) % 4 < 2) else 0
    return base


def pattern_scene_cut(i: int) -> list[list[int]]:
    if i < 60:
        return pattern_static(i)
    return [[255 if ((x // 8 + y // 8) % 2 == 0) else 0 for x in range(64)] for y in range(64)]


PATTERNS = {"static": pattern_static, "motion": pattern_motion,
            "overlay": pattern_overlay, "scene_cut": pattern_scene_cut}


def write_pgm(path: str, luma: list[list[int]]) -> None:
    h, w = len(luma), len(luma[0])
    with open(path, "wb") as fh:
        fh.write(f"P5\n{w} {h}\n255\n".encode("ascii"))
        for row in luma:
            fh.write(bytes(row))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="var/synthetic")
    ap.add_argument("--frames", type=int, default=120)
    ap.add_argument("--pattern", default="all", choices=["all", *PATTERNS.keys()])
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    names = list(PATTERNS.keys()) if args.pattern == "all" else [args.pattern]
    manifest = {"fps": 60, "streams": []}
    for name in names:
        sub = os.path.join(args.out, name)
        os.makedirs(sub, exist_ok=True)
        for i in range(args.frames):
            write_pgm(os.path.join(sub, f"{i:06d}.pgm"), PATTERNS[name](i))
        manifest["streams"].append({"name": name, "dir": sub, "frames": args.frames,
                                    "generator": PATTERNS[name].__name__})
        print(f"generated {name}: {args.frames} frames → {sub}")
    with open(os.path.join(args.out, "manifest.json"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)
    print(f"manifest: {os.path.join(args.out, 'manifest.json')}")


if __name__ == "__main__":
    main()
