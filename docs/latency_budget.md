# Latency budget (cloud_t4 profile, p99 <45ms)

| Stage | Budget | Measurement point |
|---|---|---|
| M1 decode + normalize | 12ms | `t_ingest_ns` − receive |
| M2 first-level features | 6ms | stage span |
| M3 masking | 5ms | stage span |
| M4 similarity | 5ms | stage span |
| M5 decision | 2ms | stage span |
| M6 enqueue | 3ms | stage span |
| Scheduling / buffering | 12ms | end-to-end remainder |
| Total | 45ms | `latency_ns` p99 histogram |

Gate: `tests/perf` (cloud-profile CI); live histogram: `sieve_stage_latency_seconds`;
over-budget actions: DESIGN.md §7.
