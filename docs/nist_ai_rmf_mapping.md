# NIST AI RMF 1.0 mapping (reference-implementation surface)

| Function | Implementation | Evidence |
|---|---|---|
| GOVERN | `governance/` (policy as code), audit chain | audit logs, README development principles |
| MAP | `docs/architecture.md`, `configs/schemas/` data contracts | schema files |
| MEASURE | `m7_telemetry/`, `benchmarks/` (reduction / recall / latency / energy) | benchmark reports |
| MANAGE | `pipeline/failsafe.py`, presets, incident playbook | fault-injection tests |

Planned contributions for the OWASP AI Exchange (content-safety working group):
benchmark protocol, annotation format, latency/recall baselines, fail-safe pattern.
