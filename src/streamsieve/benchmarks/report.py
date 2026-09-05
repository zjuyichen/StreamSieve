"""Report generation: artifacts for deliverables D3/D4/D5 (md/html/json/parquet).

Artifact directory: reports/<run_id>/
  - metrics.json        summary metrics
  - telemetry.parquet   per-frame telemetry (pyarrow in production; JSONL fallback here)
  - report.md / .html   human-readable report (benchmark / energy / recall chapters)
"""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field


@dataclass
class ReportBundle:
    run_id: str
    config_hash: str
    summaries: list[dict] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def emit(bundle: ReportBundle, out_root: str = "reports") -> str:
    out_dir = os.path.join(out_root, bundle.run_id)
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "metrics.json"), "w", encoding="utf-8") as fh:
        json.dump(asdict(bundle), fh, indent=2, ensure_ascii=False)
    lines = [f"# Benchmark Report `{bundle.run_id}`", "", f"- config_hash: `{bundle.config_hash}`", ""]
    for s in bundle.summaries:
        lines.append(f"## {s.get('stream_id', '?')}")
        lines.append("")
        for k, v in s.items():
            lines.append(f"- {k}: {v}")
        lines.append("")
    with open(os.path.join(out_dir, "report.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    return out_dir
