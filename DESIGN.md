# StreamSieve — Engineering Design

**High-Efficiency AI Governance & Sustainable Computational Optimization Framework**

| Field | Value |
|---|---|
| Project codename | `streamsieve` (replaceable) |
| Target platforms | local Apple-silicon dev machine (functional validation) → Google Cloud T4/L4 (metric gates) → AWS/GCP marketplaces (turnkey services) |
| Core targets | 65–80% redundant-frame reduction; >99.8% recall; <45 ms end-to-end p99; >40% compute/energy reduction; ≥10× 1080p@60fps streams with zero drops |

---

## 0. Design principles and constraints

1. **Independent implementation.** Everything in this repository is written from
   scratch for this project. No third-party proprietary source code, models,
   datasets, or confidential assets are used or adapted.
2. **Strict data boundaries.** Development and validation rely exclusively on
   public research benchmarks (UCF101, Kinetics-400, YouTube-8M subsets) and
   self-generated synthetic streams.
3. **Sandbox-only integration.** Any platform integration occurs strictly within
   authorized developer sandboxes using non-production test data under formal
   evaluation agreements.
4. **No training on evaluation data (G4).** The pipeline never trains,
   fine-tunes, or retrains models on evaluation or platform data. This is
   enforced in code (CI scan + runtime guard).
5. **Non-invertible features (G7).** External-facing or persisted visual
   representations are perceptual hashes or embeddings; raw frames are never
   persisted (G2).
6. **Human-in-the-loop primacy (G8).** The pipeline is an infrastructure
   pre-filter only; final content actions remain with platform reviewers or
   policies.
7. **Fail-safe by default (G9).** Any fault routes to 100% dispatch for review —
   never a silent skip.
8. **Measurable, reproducible claims.** Thresholds, budgets, and benchmarks are
   config-driven and reproducible via `config_hash`.

### 0.1 Governance controls G1–G10

The project codifies its data-handling commitments as ten controls, each mapped
to an enforcement point in code (details in §10):

G1 purpose limitation · G2 zero retention · G3 TLS 1.3 / AES-256 · G4 no
training · G5 least privilege · G6 timed purge (5 business days) · G7
non-invertible features · G8 human-in-the-loop primacy · G9 fail-safe · G10 full
auditability.

### 0.2 Where things change

- Feature work: `src/streamsieve/**` (modules are decoupled; each module has an
  `interfaces.py` protocol).
- Thresholds, budgets, governance switches: `configs/`.
- Design decisions and rationale: this file; focused notes in `docs/`.

---

## 1. Goals and hard targets

| # | Target | Value | Engineering means | Verification |
|---|---|---|---|---|
| I1 | Redundant-frame reduction | 65–80% | M4 fused differential score + M5 multi-tier thresholds | harness: bypassed / total |
| I2 | Safety-change recall | >99.8% | M5 safety floors (streak/time caps + keepalive), overlay-mutation force review, quadrant OR | event-level annotation replay |
| I3 | End-to-end latency | <45 ms p99 | §7 budget + micro-batching + native hot paths | perf gate + live histograms |
| I4 | Compute/energy reduction | >40% | fewer inference invocations (primary) + lightweight features (secondary) | energy sampler + audit report |
| I5 | Concurrency / stability | ≥10× 1080p@60fps; 48 h zero drops, no leaks | per-stream isolation, bounded queues, backpressure | soak scripts + RSS-slope checks |
| I6 | Fail-safe | fault → 100% review | failsafe state machine + watchdog | fault-injection tests |
| I7 | Standards alignment | NIST AI RMF 1.0 | §11 mapping | docs + audit chain |

---

## 2. Architecture

### 2.1 Data plane (per-frame pipeline; the 7 modules)

```
[Live Stream Input: RTMP / HLS / WebRTC / MP4 / Synthetic]
         │  M1 Stream Normalization Layer        → YUV/RGB tensors + 1/8 luma pyramid
         ▼
[2. Temporal Feature Extraction Engine]         64-bit pHash + 4× quadrant hashes (+ gray-zone embedding)
         ▼
[3. Spatial Risk-Region Masking] ◄── overlay / danmaku / caption / game-UI detector (region registry)
         ▼
[4. Differential Similarity Engine]              prev/anchor dual-channel deltas + quadrants + fusion
         ▼
[5. Adaptive Frame Decision Filter]              multi-tier thresholds + hysteresis + safety floors + adaptive factor
         ├── REDUNDANT (BYPASS) ─────────► [Cache & Log / Bypass]   (heavy inference skipped)
         └── REVIEW / FORCE_REVIEW ─────► [6. Review Queue Dispatcher] → platform classifier / human review
         ▼
[7. Continuous Telemetry & Logging Harness]      latency / reduction / energy / audit chain (side-path; see 2.3)
```

### 2.2 Control plane (separate fault domain)

- **Config plane**: YAML + profile overlay + JSON-Schema validation + `config_hash` (reproducibility anchor).
- **Health/mode plane**: `NORMAL / DEGRADED / FAILSAFE_BYPASS` state machine (`pipeline/failsafe.py`).
- **Audit plane**: HMAC hash-chained append-only audit log (verifiable end-to-end), separate file descriptor; write failure degrades and alerts.

### 2.3 Side-path design principles

- Telemetry (M7) must never block the decision path: the hot path only does O(1)
  counting and ring-buffer writes; aggregation and export run off-path.
- Audit write failure → data plane degrades to DEGRADED (keeps filtering) + alert;
  never silent.

### 2.4 Environment profiles

| profile | Use | Key differences |
|---|---|---|
| `local_m4` | months 1–2 functional development (Apple-silicon notebook) | CPU/MPS backends; relaxed latency budget (80 ms); synthetic streams only |
| `cloud_t4` / `cloud_l4` | months 4–6 metric gates | NVDEC decode + GPU features; 45 ms budget; full Prometheus |
| `pilot_sandbox` | platform sandbox pilots | `max_recall` preset; TLS 1.3 enforced; strict retention; mock queue |

### 2.5 Process / thread model

- One stream = one isolated async pipeline (asyncio task chain); full isolation
  between streams (fairness, fault containment).
- I/O (decode, network) runs in a thread pool (PyAV releases the GIL); M2–M4 hot
  paths call native kernels (no GIL); GPU micro-batching (≤3 frames) only when
  queue depth crosses the trigger (latency-first scheduler decision, §7.3).
- GIL strategy: pure-Python control plane; all data-plane hot paths execute in
  native code or ONNX Runtime.

---

## 3. Repository layout

```
.
├── README.md                     # overview, quickstart, principles
├── DESIGN.md                     # this document
├── CHANGELOG.md                  # release history
├── pyproject.toml                # packaging; core is dependency-free
├── Makefile / .gitignore / .dockerignore
├── LICENSE                       # Apache License 2.0
│
├── configs/
│   ├── default.yaml              # default parameters (thresholds/budgets/governance)
│   ├── profiles/                 # local_m4, cloud_t4, cloud_l4, pilot_sandbox
│   └── schemas/                  # pipeline_config.schema.json, frame_decision.schema.json
│
├── docs/
│   ├── architecture.md           # data/control-plane notes
│   ├── latency_budget.md         # 45 ms breakdown and measurement points
│   ├── data_governance.md        # G1–G10 → code locations
│   ├── nist_ai_rmf_mapping.md    # AI RMF mapping
│   ├── benchmark_protocol.md     # matched-baseline protocol and annotation format
│   ├── deliverables.md           # pilot delivery package D1–D7
│   └── templates/adoption_analysis.md
│
├── src/streamsieve/
│   ├── common/                   # ★ data contracts, clock, errors, hashing
│   ├── config/                   # loader + config_hash
│   ├── modules/
│   │   ├── m1_normalization/     # sources (rtmp/hls/webrtc/file/synthetic), decoder, frame pool
│   │   ├── m2_features/          # ★ pHash/quadrant hashes (+ optional ONNX embedding)
│   │   ├── m3_masking/           # ★ overlay detection + mutation watch, masks
│   │   ├── m4_similarity/        # ★ hamming, structural, anchor, fused scoring
│   │   ├── m5_decision/          # ★★ decision core (safety floors/hysteresis/adaptive factor)
│   │   ├── m6_dispatch/          # bounded queue, backpressure, adapters (mock/webhook)
│   │   └── m7_telemetry/         # ★ metrics registry, energy sampler, HMAC audit chain
│   ├── pipeline/                 # stage, engine, failsafe, presets, ★ reference implementation
│   ├── serving/                  # REST (FastAPI), gRPC, health, proto
│   ├── governance/               # ★ retention, crypto, authz, no-train guard, sanitizer
│   ├── benchmarks/               # ★ metrics, harness, datasets, annotations, report
│   ├── multimodal/               # Phase II: audio/text encoders, fusion, degradation
│   └── cli/                      # sieve CLI
│
├── tests/                        # unit / integration / perf / soak
├── deployments/                  # docker (cpu/gpu), helm chart, terraform (gcp)
├── native/README.md              # planned native kernels (Rust/C++ + SIMD)
├── scripts/                      # demo, synthetic generator, stress, calibration, audits, sanitize
├── third_party/licenses.md       # third-party asset registry
└── reports/                      # benchmark artifacts (not committed)
```

★ = runnable reference implementation provided; unmarked files are
interfaces/stubs to be filled per the §16 roadmap.

---

## 4. Data contracts (`common/types.py`)

| Type | Key fields | Constraints |
|---|---|---|
| `FrameEnvelope` | stream_id, seq, pts_ns, t_ingest_ns, dims/format, `luma_pyramid`, `pool_ref`, `trace` | `pool_ref` points into the frame pool; **never persisted across sessions** (G2) |
| `Descriptor` | `phash64: int`, `quad_h: tuple[int×4]`, `overlay_hash`, `embedding` | fully non-invertible representations (G7) |
| `MaskSet` | `regions: tuple[Region]`, `overlay_mutation: bool`, `overlay_score: float` | Region = kind + rect + textiness; kind ∈ {CHAT, DANMAKU, CAPTION, GAME_UI} |
| `SimilarityResult` | `fused`, `dprev`, `danchor`, `quad_q`, `quad_max`, `mad`, `scene_cut` | all distances normalized to [0,1] |
| `FrameDecision` | `outcome`, `score`, `reasons`, `mode`, latencies, `config_hash`, timestamps | external JSON Schema: `configs/schemas/frame_decision.schema.json` |
| `Outcome` | `BYPASS / REVIEW / FORCE_REVIEW / SAFETY_FLOOR / FAILSAFE` | `SAFETY_FLOOR` makes "max consecutive-bypass" measurable |
| `Mode` | `NORMAL / DEGRADED / FAILSAFE_BYPASS` | consistent with the `/mode` endpoint |

**Time basis**: `t_ingest_ns` (M1 exit) → `t_decision_ns` (M5 exit);
`latency_ns = t_decision_ns − t_ingest_ns` is the I3 definition (decode and
normalization included). All timestamps use the monotonic clock.

**Reproducibility**: every run records
`config_hash = sha256(canonical_json(config))`, attached to each frame decision
and report so benchmarks can be replayed exactly (NIST MEASURE requirement).

---

## 5. Module logic (M1–M7)

### M1 normalization (`m1_normalization/`)
- **Responsibility**: standardize heterogeneous inputs (RTMP/HLS/WebRTC/MP4 and
  synthetic streams) into a canonical tensor: `YUV420p` main frame + a
  pre-computed 1/8-resolution luma pyramid (the only source read by later
  lightweight modules).
- **Implementation notes**: PyAV/FFmpeg decode (NVDEC on cloud, VideoToolbox on
  local Macs); decode thread pool decoupled from the GIL; ring-buffer frame pool
  with zero-copy refcounting and zero-fill on release (G6-aligned); `t_ingest_ns`
  stamped at normalization completion.
- **Failure modes**: decode error rate >1% over a sliding window → stream enters
  fail-safe; irregular pts → linear interpolation + `pts_latch` flag.

### M2 temporal features (`m2_features/`)
- **Responsibility**: low-overhead spatial-temporal descriptors: frame-level
  64-bit pHash + four 16-bit quadrant hashes (+ optional lightweight embedding).
- **Cascade strategy (the core compute saver)**: level 1 (every frame) = SIMD
  hashes, target ≤1 ms per 1080p frame; level 2 (gray-zone only) = ONNX
  embedding (open-licensed model), results written back to
  `Descriptor.embedding` for M4 fusion.
- **Spec**: 1080p → 1/8 pyramid (135×240) → 32×32 luma → DCT → median of the low
  8×8 → 64 bits. Pure-Python reference in `phash.py`; production uses `native/`.
- **Failure modes**: embedding timeout → continue with level-1 hashes (degrade,
  don't fail) and count the event.

### M3 spatial risk-region masking (`m3_masking/`)
- **Responsibility**: detect and track high-interaction regions (danmaku, chat,
  captions, game UI) and emit `MaskSet`.
- **Algorithm**: tile textiness map (edge density × stroke consistency on the 1/8
  pyramid); sliding-window voting → stable region registry with tracking;
  **overlay-mutation watch**: binarized region hash per registered region —
  a hash change > ε sets `overlay_mutation=True` (OCR-free "text changed"
  detection).
- **Dual role (the key safety design)**: mutation → M5 issues FORCE_REVIEW
  (protects against downsampling misses of moderated overlay text); active overlay
  quadrants cannot be counted as "purely static redundant" — weight multiplied by
  `overlay_sensitivity`.
- **Failure modes**: detector failure → conservative mode (all tiles treated as
  text; everything force-reviewed).

### M4 differential similarity (`m4_similarity/`)
- **Dual-channel differencing**: `dprev` (vs previous frame; catches instant
  jumps) and `danchor` (vs the anchor frame; catches accumulated drift).
- **Anchor management (drift prevention)**: the anchor refreshes only when a frame
  is dispatched for REVIEW/FORCE_REVIEW/SAFETY_FLOOR or a scene cut is detected —
  the reference point is always a frame that received a full safety check.
- **Fusion score** (`scoring.py`, weights configurable):
  `fused = w_p·dprev + w_a·danchor + w_m·mad + w_c·(1−ssim_lite)`, default
  `(0.45, 0.30, 0.15, 0.10)`; `quad_max = max(quadrant deltas)`; quadrant-OR
  logic keeps local jumps from being averaged away.
- **Failure modes**: NaN/out-of-range → treated as `fused=1.0` (force review).

### M5 adaptive frame-decision filter (`m5_decision/`) ★ core
Decision order (safety first):

```
0) Mode == FAILSAFE_BYPASS        → Outcome.FAILSAFE (dispatch everything; G9)
1) force-review signals (any hit) → FORCE_REVIEW
   mask.overlay_mutation | quad_max ≥ t_force | scene_cut
2) safety floors (before any bypass; hard caps):
   a) consecutive-bypass interval ≥ bypass_streak_max_frames → SAFETY_FLOOR
   b) interval time + dt ≥ bypass_streak_max_seconds        → SAFETY_FLOOR
   c) keepalive due (≥ keepalive_every_seconds)             → SAFETY_FLOOR
3) tiered scoring:
   score ≤ t_bypass × k   → BYPASS   (k = adaptive factor, clamped [0.5, 2.0])
   score < t_gray_upper   → hysteresis: REVIEW after `hysteresis_frames`; else BYPASS
   score ≥ t_gray_upper   → REVIEW (gradual change)
```

- **Design invariants (asserted in tests)**: INV1 dispatch frame gap ≤
  `bypass_streak_max_frames`; INV2 dispatch time gap ≤
  max(`bypass_streak_max_seconds`, keepalive); INV3 force-review channel never
  affected by the adaptive factor; INV4 lower thresholds ⇒ monotone
  non-decreasing recall (basis for calibration).
- **Failure modes**: corrupted state → reset to conservative initial state
  (streak = cap − 1) + event counted.

### M6 review-queue dispatch (`m6_dispatch/`)
- **Responsibility**: dispatch review frames to platform classifiers / human
  queues / sandbox mock endpoints.
- **Backpressure policy (explicit priorities)**: REVIEW > FORCE_REVIEW
  escalation > telemetry. When the bounded queue is full, telemetry capacity is
  evicted first; REVIEW frames are never silently dropped; if the REVIEW queue
  stays full → circuit breaker → the stream enters fail-safe (full review) +
  alert.
- **Adapters**: `mock_queue.py` (HTTP mock of an enterprise review flow;
  sandbox standard), `webhook.py` (REST; TLS 1.3 enforced), Kafka reserved;
  exponential backoff + idempotency key (`stream_id:seq`).
- **Failure modes**: 3 consecutive HTTP 5xx → breaker open 30 s; the stream
  fail-safes in the meantime.

### M7 continuous telemetry & logging (`m7_telemetry/`)
- **Metric namespace `sieve_*` (single registry `metrics.py`)**:
  `sieve_frames_total{stream,outcome}`, `sieve_bypass_ratio`,
  `sieve_stage_latency_seconds{stage}`, `sieve_queue_depth{stage}`,
  `sieve_energy_joules_total{device}`, `sieve_failsafe_activations_total`,
  `sieve_recall_probe_total`, `sieve_audit_write_failures_total`,
  `sieve_frames_dropped_total` (soak gate: must stay 0).
- **Energy sampling** (`energy.py`): GPU via NVML (power integration; energy
  counters where available), CPU via Linux RAPL; dev macOS uses powermetrics
  (approximate, flagged). All values in joules; raw samples retained for audit.
- **Audit log** (`audit_log.py`) ★: JSONL with `prev_hmac → hmac` chaining;
  `sieve audit-verify` validates the whole chain; records session start/stop,
  mode changes, purge events, rule triggers.
- **Reports**: each benchmark run produces `reports/<run_id>/{metrics.json,
  telemetry.parquet, report.md, report.html}`.

---

## 6. Decision thresholds and presets

| Parameter | balanced | max_recall (sandbox default) | throughput | Notes |
|---|---|---|---|---|
| `t_bypass` | 0.020 | 0.012 | 0.030 | below → redundant candidate |
| `t_gray_upper` | 0.060 | 0.045 | 0.080 | gray-zone upper bound |
| `t_force` | 0.120 | 0.090 | 0.150 | force-review threshold |
| `hysteresis_frames` | 2 | 1 | 3 | gray-zone hysteresis |
| `bypass_streak_max_frames` | 150 (2.5s @60) | 90 (1.5s) | 240 | bypass-streak frame cap |
| `bypass_streak_max_seconds` | 2.5 | 1.5 | 4.0 | bypass-streak time cap |
| `keepalive_every_seconds` | 5.0 | 3.0 | 10.0 | keepalive sampling |
| `overlay_sensitivity` | 1.5 | 2.0 | 1.2 | overlay-region weight |

**Calibration** (`scripts/calibrate_thresholds.py`): grid/bisection search over
the benchmark set, maximizing the reduction ratio s.t. event-level recall ≥
99.8% and p99 latency ≤ 45 ms. Output: profile YAML patch + calibration report
(attached to the benchmark report appendix).

---

## 7. Latency budget (<45 ms p99, cloud_t4 profile)

| Stage | p99 budget | Measurement point | Over-budget action |
|---|---|---|---|
| M1 decode + normalize (incl. pyramid) | 12 ms | `t_ingest_ns` − receive | alert; sustained → degrade (skip pyramid pre-compute) |
| M2 features (level 1) | 6 ms | stage span | alert; disable level-2 embedding |
| M3 masking | 5 ms | stage span | alert; reduce tile refresh rate (conservative mode) |
| M4 similarity | 5 ms | stage span | alert |
| M5 decision | 2 ms | stage span | expected <1 ms; 2 ms indicates a problem |
| M6 enqueue | 3 ms | stage span | alert |
| Scheduling / buffering / serialization | 12 ms | end-to-end remainder | inspect micro-batching and lock contention |
| **Total** | **45 ms** | `latency_ns` p99 histogram | CI perf gate (`tests/perf`) |

**Measurement rule**: end-to-end latency is defined as "frame enters M1 →
decision completes in M5". The perf gate regresses ≥1k frames/scenario in
cloud-profile CI and fails on budget overruns.

---

## 8. Fail-safe and degradation (`pipeline/failsafe.py`)

### 8.1 Trigger table

| Trigger | Detection | Action |
|---|---|---|
| Stage heartbeat timeout (>100 ms, 3 strikes) | watchdog | stream → FAILSAFE_BYPASS |
| Decode/GPU error rate >1% (30 s window) | counters | stream → FAILSAFE_BYPASS |
| REVIEW-queue circuit breaker (§M6) | queue monitor | stream → FAILSAFE_BYPASS |
| M5 state corruption / non-finite values | assertion | single frame FORCE_REVIEW + state reset |
| Audit write failure | exception capture | global → DEGRADED (keep working) + alert escalation |
| Process crash | K8s liveness | pod restart; no stream intake before ready |

### 8.2 State machine and recovery

```
NORMAL ──(trigger)──► FAILSAFE_BYPASS ──(30 s cooldown + 10 s healthy probe)──► NORMAL
   │                       ▲
   └──(write failure)──► DEGRADED ─(recovery)─┘
```

- FAILSAFE_BYPASS means **100% dispatch for review** (trade filtering gains for
  zero missed content) — the direct implementation of G9.
- Exit probe: a 10 s synthetic micro-stream must pass end-to-end with normal p99
  before leaving fail-safe; flap suppression (no double-entry counting within
  60 s).
- All transitions are written to the audit chain +
  `sieve_failsafe_activations_total`.

### 8.3 Fault-injection tests

Inject, one at a time: stage exception, heartbeat stop, queue saturation, NaN
scores, read-only audit disk — assert everything routes to fail-safe and the
audit chain verifies.

---

## 9. Benchmark framework (matched baseline, `benchmarks/`)

### 9.1 Flow

```
for scenario in [static/low-motion, gaming, e-commerce, high-action sports, mixed synthetic]:
    1) control run : all frames → safety-inference stand-in (classifier proxy, open-licensed)
    2) filtered run: StreamSieve pipeline + the same stand-in
    — both runs: same hardware, same baseline config, fixed seeds, recorded config_hash
    compute: reduction ratio / event recall / frame recall / FP distribution /
             latency percentiles / energy per kframe / throughput
artifacts: reports/<run_id>/ (per-frame telemetry.parquet + metrics.json + report.md/html)
```

- **Classifier stand-in**: during sandbox phases an open-licensed lightweight
  classifier stands in for the platform model so the energy/latency comparison
  is closed-loop; the real platform model connects through the same adapter
  interface inside an authorized sandbox.
- **Latency scope**: the control "all frames" path measures inference-side cost
  only; the I3 <45 ms target binds only StreamSieve's ingest → decision segment
  (avoids mixing the two metrics).

### 9.2 Event annotation format (ground truth, `annotations.py`)

```json
{
  "stream_id": "ucf101/basketball/v1",
  "fps": 60,
  "events": [
    {"event_id": "e12", "type": "risk_delta|overlay_mutation|scene_change|static",
     "start_frame": 1820, "end_frame": 1852, "quadrants": ["q2"],
     "label": "violent_gesture", "severity": "high"}
  ]
}
```

- **Event-level recall** = events correctly dispatched (REVIEW/FORCE_REVIEW/
  SAFETY_FLOOR) / total annotated events; an event hits if at least one frame in
  its window is dispatched. Target: >99.8% (I2). The missed-event list is
  emitted for root-cause analysis.
- **Frame-level recall** = dispatched frames within annotated windows / total
  window frames (a stricter diagnostic).

### 9.3 Metric formulas (`metrics.py`, single source of truth)

| Metric | Formula |
|---|---|
| Redundant reduction | `bypassed / total_frames` |
| Event recall | `hit_events / total_events` |
| Latency percentiles | `percentile(latency_ns, [50, 95, 99])` |
| Energy per kframe | `Σ joules / (frames / 1000)`, grouped filter/control |
| Inference-compute saving | `1 − Σ(filtered inference joules) / Σ(control inference joules)` |
| Annual kWh extrapolation | `kWh/day × 365 × channels` (measured values and assumptions in the audit appendix) |

### 9.4 Report artifacts → delivery mapping

| Deliverable | Artifact |
|---|---|
| D3 benchmark telemetry report | `report.md/html` + `telemetry.parquet` |
| D4 hardware/energy audit | `energy_audit` chapter + `scripts/energy_audit.py` output |
| D5 recall & latency audit | event-recall table + latency histogram + missed-event list |
| D7 open-source sanitization review | `scripts/opensource_sanitize.py` output |

---

## 10. Data governance controls G1–G10 (code locations)

| Control | Code location | Mechanism |
|---|---|---|
| G1 purpose limitation | `configs/pilot_sandbox.yaml` + docs | config gate + session-purpose field |
| G2 zero retention | `governance/retention.py` | frames never persisted; session temp TTL 24h |
| G3 encryption (TLS 1.3 / AES-256) | `governance/crypto.py` + `serving/` | adapters enforce TLS 1.3; at-rest AES-256-GCM |
| G4 no training | `governance/no_train_guard.py` | CI static scan (no optimizer/backward) + runtime guard |
| G5 least privilege | `governance/authz.py` | `sandbox.*` scope allowlist; MFA upstream |
| G6 timed purge (5 business days) | `governance/sanitizer.py` | `sieve sanitize` + scheduler; every purge audited |
| G7 non-invertible features | `m2_features/` | only hashes/embeddings leave the module |
| G8 human-in-the-loop primacy | architectural (M6 dispatches only) | no autonomous enforcement; decisions carry `human_review_required` |
| G9 fail-safe | `pipeline/failsafe.py` | fault → 100% dispatch to review |
| G10 full auditability | `m7_telemetry/audit_log.py` | hash chain + export interface for platform engineers |

---

## 11. NIST AI RMF 1.0 mapping

| AI RMF function | Implementation |
|---|---|
| GOVERN | `governance/` (policy as code) + audit chain + provenance principles (§0) |
| MAP | `docs/architecture.md` + `configs/schemas/` (explicit data contracts) |
| MEASURE | `m7_telemetry/` + `benchmarks/` (reduction / recall / latency / energy) |
| MANAGE | `pipeline/failsafe.py` + presets + incident playbook (to be added) |

**OWASP AI Exchange (content-safety WG) contributions**: this benchmark
protocol + annotation format + latency/recall baselines + the fail-safe pattern
(drafting begins in month 6).

---

## 12. Deployment and cloud (months 3–5)

### 12.1 Containers
- `Dockerfile.cpu`: python:3.11-slim + ffmpeg runtime libraries (local/demo).
- `Dockerfile.gpu`: nvidia/cuda + NVDEC + onnxruntime-gpu (cloud GPU standard).
- Multi-stage builds; runtime images carry no toolchain; SBOM (syft) + image
  signing (cosign).

### 12.2 Helm (`deployments/helm/streamsieve`)
- Key values: `replicaCount`, `gpu.enabled/resources`, probes
  (`/healthz`, `/readyz`), Prometheus annotations, resource limits, secrets
  (`envFrom`: audit HMAC key).
- HPA metrics: `sieve_queue_depth` and `sieve_stage_latency_seconds` (not raw
  CPU).

### 12.3 GCP stress topology (months 4–5)
- GKE + T4/L4 node pools; object storage (synthetic streams / annotations);
  Cloud Monitoring scrapes Prometheus.
- 10× 1080p@60fps for 48 h: zero frame drops
  (`sieve_frames_dropped_total == 0`), RSS slope <1 MB/h, constant FD count;
  a stability report is produced.

### 12.4 Sandbox pilot surface
- Integration: REST (`/v1/sessions` to register a synthetic stream,
  `/v1/decisions/{stream}` for decision streaming) + gRPC (`Ingest` /
  `DecisionStream`); the mock queue endpoint simulates enterprise review flows.
- Activity ledger: candidates → contacted → scoping → pilot → sandbox →
  concluded → licensing; each step records only what has actually happened.

---

## 13. CI/CD and quality gates

```
push/PR →
 1) lint (ruff) + type (mypy) + config schema validation
 2) unit + integration (decision golden tests, fault injection, audit-chain verification)
 3) governance scans: no-training patterns + license scan
 4) perf gate: tests/perf (p99 budget regression, cloud profile)
 5) container builds (cpu/gpu) + SBOM + vulnerability scan
nightly: shortened soak (4 h); pre-release: full 48 h soak + energy audit
```

---

## 14. Open-source surface and sanitization (month 6)

### 14.1 Boundary matrix

| Component | Open source (Apache-2.0) | Reserved (commercial/licensing) |
|---|---|---|
| M1 connectors / normalization | yes | — |
| Data contracts and JSON schemas | yes | — |
| Benchmark framework (harness/annotations/metrics) | yes | — |
| M2 basic hash reference | yes | native SIMD kernels |
| M3/M4 basic implementations | partial (connector layer) | fusion algorithms, adaptive parameters |
| M5 decision core (safety floors / adaptive) | — | yes |
| M7 audit chain | yes | managed-service packaging |

### 14.2 Sanitization flow (`scripts/opensource_sanitize.py`, D7)

1. Copy files per the whitelist manifest;
2. scan and strip: platform-specific configs, secrets, internal endpoints,
   tuned threshold values;
3. inject Apache-2.0 headers + NOTICE; emit a per-file-hash review report.

---

## 15. Phase II: multimodal extension (months 7–12, `multimodal/`)

- **Interface reserved**: all modalities share `ModalitySignal` (kind, ts,
  score, features, reliability).
- **Audio**: open-source self-supervised acoustic encoder (event head), 16 kHz,
  budget ≤8 ms per frame group.
- **Text**: streaming NLP encoder for chat/danmaku, window-aggregated.
- **Fusion**: `fusion.py` cross-modal attention layer aligning visual/audio/text
  tokens on a shared timeline; its risk score joins the M5 force-review channel
  (the safety-floor invariants do not change).
- **Graceful degradation**: a missing or low-confidence modality forces human
  escalation for that window — never a default-safe assumption.
- **Engineering shape**: multimodal stages assemble declaratively in
  `engine.py`; single-modality performance paths stay unaffected.

---

## 16. Implementation roadmap (months 1–6)

| Month | Tasks | Repository focus | Acceptance |
|---|---|---|---|
| 1 | Architecture formalization, testbed setup, pilot documentation | this skeleton + `docs/` + synthetic generator + config schemas | `make validate` + demo pass |
| 2–3 | Core engine implementation, containerization, baseline benchmarking | fill M1–M7 (native kernels) → Docker/Helm → run the harness over the five scenario classes | first harness report; container images run |
| 4–5 | Queue integration, cloud stress testing, pilot scoping | GCP cluster 10-stream 48 h; `mock_queue` integration; scenario-specific tuning | soak report (zero drops); activity ledger initialized |
| 6 | Benchmark reporting, open-source sanitization, transition | final report + `opensource_sanitize` + OWASP drafting | delivery package D1–D7 complete |

---

## 17. Risks and trade-offs

| Risk | Impact | Mitigation |
|---|---|---|
| Python GIL limits throughput | hard to hit latency | hot paths in native kernels; Python for orchestration only; early perf gates |
| Threshold calibration overfits test sets | production recall drop | multi-scenario cross-validation; safety floors are structural, not threshold-dependent |
| Micro-batching raises throughput but adds latency | p99 breach | enable only above queue-depth trigger; monitor latency histograms |
| Energy-methodology disputes | audit credibility | retain raw samples + explicit extrapolation assumptions (§9.3) |
| Sandbox vs production gap | adoption friction | unified classifier-proxy interface; pilots integrate the real platform adapter |
| Overlay-detector false positives | lower reduction ratio | conservative mode degrades gracefully; tuning recorded in calibration reports |

---

## 18. Appendix

- **A. Threshold quick reference**: see §6 and `configs/default.yaml`.
- **B. Metric names**: full `sieve_*` set in
  `src/streamsieve/modules/m7_telemetry/metrics.py`.
- **C. Glossary**: Danmaku = bullet-comment overlays; Bypass = safe skip of heavy
  inference; Safety Floor = consecutive-bypass cap; Anchor = most recently
  reviewed frame; Matched Baseline = same-environment unfiltered control.
- **D. Change log**: see `CHANGELOG.md`.
