# Architecture notes (see DESIGN.md §2–§5)

Data plane: M1 normalization → M2 features → M3 masking → M4 similarity → M5 decision → (BYPASS | REVIEW) → M6 dispatch; M7 rides alongside for telemetry.
Control plane: config + health/mode (failsafe) + audit chain, with fault-domain isolation from the data plane.

Key engineering decisions:
1. **Cascaded features**: the first-level hash runs on every frame; the second-level embedding fires only in the gray zone (saves compute).
2. **Drift-proof anchoring**: differencing is always against the most recently reviewed frame, keeping the safety reference fresh.
3. **Safety floors**: frame/time caps on consecutive bypass plus keepalive sampling make recall independent of threshold-tuning precision.
4. **Fail-safe**: any fault → 100% dispatch to review (fail-safe, never fail-open).
5. **Side-path telemetry**: M7 never blocks the decision path; write failures degrade to DEGRADED with an alert.
