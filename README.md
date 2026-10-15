# StreamSieve

> **High-Efficiency AI Governance & Sustainable Computational Optimization Framework**
> An adaptive, low-latency pre-filter for live-video safety pipelines.

StreamSieve sits in front of heavy safety classifiers as a lightweight adaptive
filter. Visually redundant frames — static scenes, unchanged overlays, low-motion
segments — are safely bypassed, and only risk-relevant deltas are dispatched to
deep safety inference or human review. The result is a large reduction in compute
and energy consumption per stream, without sacrificing safety coverage.

## Why it exists

- Live-video safety inference is one of the most sustained compute loads in
  modern data centers.
- Static and low-motion frames dominate real livestreams, so a large share of
  inference work is redundant.
- Safety classifiers are heavyweight; a cheap pre-filter that preserves recall
  removes redundant work at the source.

## Hard targets

| # | Metric | Target | Enforced by |
|---|---|---|---|
| I1 | Redundant-frame reduction | 65–80% | matched-baseline harness |
| I2 | Safety-change recall | >99.8% | event-level replay + safety floors (M5) |
| I3 | End-to-end latency (ingest → decision) | <45 ms p99 | latency budget + perf gate |
| I4 | Compute/energy reduction | >40% GPU/CPU | energy sampler + audit report |
| I5 | Concurrency | ≥10× 1080p@60fps, zero frame drops, 48 h soak | soak scripts |
| I6 | Fail-safe | any fault → 100% review | pipeline/failsafe.py |
| I7 | Standards alignment | NIST AI RMF 1.0 | docs/nist_ai_rmf_mapping.md |

## Quick start

```bash
# validate the default configuration (no third-party deps needed)
PYTHONPATH=src python3 -m streamsieve.cli.main validate-config --config configs/default.yaml

# reference-implementation demo (pure Python; correctness/teaching, not the performance path)
PYTHONPATH=src python3 scripts/demo_reference.py

# generate synthetic streams (sandbox fixtures; no dataset required)
PYTHONPATH=src python3 scripts/gen_synthetic_stream.py --out var/synthetic --frames 300

# tests (needs pytest)
pip install -e ".[dev]" && pytest tests/unit -q
```

## Layout

```
src/streamsieve/
├── modules/          # the 7 decoupled modules (M1–M7)
├── pipeline/         # engine, stage abstraction, fail-safe, presets, reference implementation
├── serving/          # REST / gRPC integration surfaces
├── governance/       # data-governance controls G1–G10, implemented in code
├── benchmarks/       # NIST-aligned matched-baseline harness
├── multimodal/       # Phase II (months 7–12) extension points
└── cli/              # the `sieve` command-line entry point
```

See **DESIGN.md** for the full design, and `docs/` for focused notes.

## Development principles

- Independent, from-scratch implementation; no third-party proprietary code.
- Development and validation use public research datasets and self-generated
  synthetic streams only.
- Platform integration happens exclusively in authorized sandboxes with
  non-production data.
- No model training on evaluation or platform data (enforced in code, G4).
- Non-invertible visual features only (perceptual hashes); raw frames are never
  persisted (G2/G7).
- Human-in-the-loop remains the final authority; the pipeline only pre-filters.
- Any fault degrades to 100% review (fail-safe, never fail-open; G9).

## Status

| Milestone | Status |
|---|---|
| Architecture and interface design (this skeleton) | complete |
| M5 decision core, similarity, audit chain (reference implementations) | runnable |
| M1–M7 production implementations (native kernels + GPU path) | pending — months 2–3 |
| Containerization and cloud stress tests (10× streams / 48 h) | pending — months 3–5 |
| Benchmark report and Apache-2.0 open-source split | pending — month 6 |

## License

Apache License 2.0 — see [LICENSE](LICENSE). The planned open-source surface
(core connectors, data contracts, benchmark harness) is described in DESIGN.md §14.
