"""Dataset loaders: UCF101 / Kinetics-400 / YouTube-8M subsets / synthetic streams.

Rules:
- only public research benchmarks and self-generated synthetic data;
- loaders must record dataset provenance and license (third-party registry);
- no entry point for any platform production data.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DatasetSpec:
    name: str
    root: str
    license_note: str
    fps: float = 30.0


UCF101 = DatasetSpec(name="ucf101", root="", license_note="research use; see dataset terms")
KINETICS400 = DatasetSpec(name="kinetics400", root="", license_note="research use; see dataset terms")
SYNTHETIC = DatasetSpec(name="synthetic", root="var/synthetic", license_note="self-generated")


def load_spec(name: str, root: str) -> DatasetSpec:  # pragma: no cover - stub
    base = {"ucf101": UCF101, "kinetics400": KINETICS400, "synthetic": SYNTHETIC}.get(name)
    if base is None:
        raise ValueError(f"unknown dataset: {name}")
    return DatasetSpec(name=base.name, root=root or base.root, license_note=base.license_note, fps=base.fps)
