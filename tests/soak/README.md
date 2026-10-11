# 48-hour soak test (stability / leaks)

Purpose: validate I5 (≥10 concurrent 1080p@60fps streams, 48 h, zero frame
drops, no memory leaks).

Run (months 4-5, GCP cluster):
```bash
bash scripts/stress_test_10x1080p60.sh   # starts 10 synthetic streams
# watch: sieve_frames_dropped_total == 0; RSS slope < 1MB/h; FD count constant
```

Acceptance:
- `sieve_frames_dropped_total` stays at 0 throughout;
- process RSS linear-regression slope < 1MB/h;
- FD count fluctuation ≤ ±2;
- the p99 latency histogram does not drift over time (snapshot comparison every 6 h).
