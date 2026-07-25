"""Three presets: balanced / max_recall / throughput (threshold table in DESIGN.md §6)."""
from __future__ import annotations

from ..modules.m5_decision.decision import DecisionConfig

PRESETS: dict[str, dict] = {
    "balanced": dict(t_bypass=0.020, t_gray_upper=0.060, t_force=0.120, hysteresis_frames=2,
                     bypass_streak_max_frames=150, bypass_streak_max_seconds=2.5, keepalive_every_seconds=5.0,
                     overlay_sensitivity=1.5),
    "max_recall": dict(t_bypass=0.012, t_gray_upper=0.045, t_force=0.090, hysteresis_frames=1,
                       bypass_streak_max_frames=90, bypass_streak_max_seconds=1.5, keepalive_every_seconds=3.0,
                       overlay_sensitivity=2.0),
    "throughput": dict(t_bypass=0.030, t_gray_upper=0.080, t_force=0.150, hysteresis_frames=3,
                       bypass_streak_max_frames=240, bypass_streak_max_seconds=4.0, keepalive_every_seconds=10.0,
                       overlay_sensitivity=1.2),
}


def decision_config_from(profile: str, overrides: dict | None = None) -> DecisionConfig:
    params = dict(PRESETS.get(profile, PRESETS["balanced"]))
    if overrides:
        params.update({k: v for k, v in overrides.items() if k in DecisionConfig.__dataclass_fields__})
    return DecisionConfig(**params)
