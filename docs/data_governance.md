# Data governance controls G1–G10 (code locations)

| ID | Control | Implementation |
|---|---|---|
| G1 | Purpose limitation | `configs/pilot_sandbox.yaml`; session purpose field |
| G2 | Zero retention | `governance/retention.py` (frames never persisted; temp-dir TTL) |
| G3 | TLS 1.3 / AES-256 | `governance/crypto.py` + enforced in `serving/` |
| G4 | No training | `governance/no_train_guard.py` (CI scan + runtime guard) |
| G5 | Least privilege | `governance/authz.py` (scope allowlist + MFA) |
| G6 | 5-business-day purge | `governance/sanitizer.py` + `sieve sanitize` |
| G7 | Non-invertible features | `m2_features/` (hashes/embeddings only) |
| G8 | Human-in-the-loop primacy | M6 only dispatches; decisions carry `human_review_required` |
| G9 | Fail-safe | `pipeline/failsafe.py` (100% dispatch on fault) |
| G10 | Full auditability | `m7_telemetry/audit_log.py` (HMAC chain + verify) |
