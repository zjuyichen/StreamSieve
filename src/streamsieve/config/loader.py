"""Configuration loading: defaults + profile overlay → validation → config_hash.

Design constraints enforced here (in code, not just docs):
- governance.retention.persist_raw_frames must be false (G2 zero retention)
- governance.training.allowed must be false (G4 no training)
- profile overlay is a deep merge (recursive dicts; scalars override).
"""
from __future__ import annotations

import copy
import os
from typing import Any

from ..common.errors import ConfigError
from ..common.hashing import config_hash


def _deep_merge(base: dict, overlay: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in overlay.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


def _load_yaml(path: str) -> dict:
    """YAML loading: pyyaml preferred; falls back to the system Ruby (Psych) parser when pyyaml is unavailable."""
    try:
        import yaml  # noqa: PLC0415
    except ImportError:
        data = _load_yaml_via_ruby(path)
    else:
        with open(path, "r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        raise ConfigError(f"config must be a mapping: {path}")
    return data


def _load_yaml_via_ruby(path: str) -> dict:
    """Fallback path: ruby -ryaml -rjson → JSON output (macOS ships Ruby)."""
    import json  # noqa: PLC0415
    import shutil  # noqa: PLC0415
    import subprocess  # noqa: PLC0415

    ruby = shutil.which("ruby")
    if not ruby:
        raise ConfigError("pyyaml (pip install pyyaml) or system ruby is required to parse YAML config")
    try:
        out = subprocess.run(  # noqa: S603
            [ruby, "-ryaml", "-rjson", "-e",
             'puts JSON.generate(YAML.load_file(ARGV[0]))', path],
            capture_output=True, text=True, timeout=15, check=True,
        )
    except (subprocess.SubprocessError, OSError) as exc:
        raise ConfigError(f"YAML parse failed (ruby fallback): {exc}") from exc
    return json.loads(out.stdout)


def load_config(path: str, profile_path: str | None = None) -> dict:
    """Load and merge configuration; returns a ready-to-use dict including '_config_hash'."""
    if not os.path.exists(path):
        raise ConfigError(f"config not found: {path}")
    cfg = _load_yaml(path)
    if profile_path:
        if not os.path.exists(profile_path):
            raise ConfigError(f"profile not found: {profile_path}")
        cfg = _deep_merge(cfg, _load_yaml(profile_path))
    validate_config(cfg)
    cfg["_config_hash"] = config_hash({k: v for k, v in cfg.items() if not k.startswith("_")})
    return cfg


def validate_config(cfg: dict) -> None:
    """Guardrail validation (core constraints mirrored in pipeline_config.schema.json)."""
    gov = cfg.get("governance", {})
    if gov.get("retention", {}).get("persist_raw_frames", False):
        raise ConfigError("G2 violation: persist_raw_frames must be false")
    if gov.get("training", {}).get("allowed", False):
        raise ConfigError("G4 violation: training.allowed must be false")
    dec = cfg.get("decision", {})
    if not (0 < dec.get("t_bypass", 0.02) < dec.get("t_gray_upper", 0.06) < dec.get("t_force", 0.12)):
        raise ConfigError("thresholds must satisfy 0 < t_bypass < t_gray_upper < t_force")
    fs = cfg.get("failsafe", {})
    if fs.get("probe_s", 10) <= 0:
        raise ConfigError("failsafe.probe_s must be > 0 (a probe is required before leaving fail-safe)")
