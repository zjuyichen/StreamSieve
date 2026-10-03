#!/usr/bin/env python3
"""Threshold calibration: maximize the reduction ratio s.t. event recall ≥ 99.8% and p99 latency ≤ 45 ms.

Method (INV4 monotonicity): grid search or bisection over t_bypass / t_gray_upper / t_force;
replay the reference implementation or the production engine over the scenario set; emit candidate profile patches and a calibration report.

Status: wired in months 2–3 (depends on harness.datasets and annotations).
"""
from __future__ import annotations


def main() -> None:  # pragma: no cover
    raise NotImplementedError("calibration script pending (months 2–3)")


if __name__ == "__main__":
    main()
