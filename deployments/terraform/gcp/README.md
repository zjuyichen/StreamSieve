# GCP stress-test environment (months 4-5)

Goal: a GKE cluster with T4/L4 node pools carrying 10× 1080p@60fps synthetic
streams for 48 h (acceptance criteria: tests/soak/README.md).

Planned modules (Terraform implementation pending):
- `google_container_cluster` + two node pools (g2-standard-8/T4, g2-standard-12/L4, `count = 1` to start);
- GCS buckets: synthetic streams and annotations (read); report artifacts (write);
- Cloud Monitoring: scrape Prometheus metrics (sieve_*) + alerts (p99 breach, failsafe trigger, drops > 0);
- Budget alert: monthly ≤ $3,000.

Cost estimate (reference; recalibrate against current pricing):
a T4 pilot is on the order of $2,100/month.
