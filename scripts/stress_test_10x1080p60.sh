#!/usr/bin/env bash
# 10x 1080p@60fps stress test (local simplified version; cluster version in deployments/terraform/gcp)
# Acceptance: sieve_frames_dropped_total == 0; RSS slope < 1MB/h; FD count constant (see tests/soak/README.md)
set -euo pipefail

CONFIG="${1:-configs/profiles/cloud_t4.yaml}"
DURATION_S="${2:-60}"
RUNS=10

echo "[stress] config=$CONFIG concurrency=$RUNS duration=${DURATION_S}s"
for i in $(seq 1 "$RUNS"); do
  # months 2-3 wiring: python -m streamsieve.cli.main run --config "$CONFIG" --stream synthetic:$i &
  echo "  - stream $i: pending wiring (sieve run --stream synthetic:$i)"
done
wait || true
echo "[stress] done (skeleton; once wired it reports zero-drop / memory-slope verdicts)"
