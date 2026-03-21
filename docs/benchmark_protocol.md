# Matched-baseline benchmark protocol (NIST-aligned)

1. Scenario set: static/low-motion, gaming, e-commerce, high-action sports, mixed synthetic (≥3 clips per class, ≥1k frames per clip).
2. Control design: control (all-frames inference stand-in) vs filtered (this pipeline + the same stand-in); identical hardware, identical baseline config, fixed seeds; record `config_hash`.
3. Metrics: redundant-frame reduction, event-level recall (>99.8%), frame-level recall, false-positive distribution, latency p50/p95/p99 (<45ms), energy per 1k frames, throughput.
4. Annotation format: `events[] {event_id, type, start_frame, end_frame, quadrants, label, severity}`.
5. Artifacts: `reports/<run_id>/{metrics.json, telemetry.parquet, report.md, report.html}`.
6. Replay: the full chain can be replayed from `config_hash` + annotations + raw telemetry.
