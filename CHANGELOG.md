# Changelog

All notable changes to the StreamSieve project are documented here.

## [0.1.0] — 2026-10-15

Initial engineering skeleton and reference implementation.

- Design documentation for the 7-module stream pre-filtering architecture
  (`DESIGN.md`, `docs/`).
- Reference implementation (pure Python): perceptual frame hashing, differential
  similarity scoring, adaptive frame-decision filter with safety floors, and
  anchor-frame management (`src/streamsieve/`).
- Data contracts, configuration profiles, and validation (`configs/`).
- Governance controls G1–G10 implemented in code: no-training guard, retention
  policy, timed purge, and hash-chained audit log
  (`src/streamsieve/governance/`, `src/streamsieve/modules/m7_telemetry/`).
- Benchmark harness scaffolding: matched-baseline runner, metrics, and report
  emitter (`src/streamsieve/benchmarks/`).
- Deployment scaffolding: Docker images (CPU/GPU), Helm chart, and GCP notes
  (`deployments/`).
- Test suite: decision golden tests, similarity tests, and a synthetic
  end-to-end test (14 tests).
