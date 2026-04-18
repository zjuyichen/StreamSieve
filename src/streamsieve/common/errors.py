"""Error types. Classification rule: anything that should route to fail-safe inherits FailSafeError."""
from __future__ import annotations


class StreamSieveError(Exception):
    """Base class."""


class FailSafeError(StreamSieveError):
    """Error that triggers fail-safe for the stream (dispatch 100% to review)."""


class ConfigError(StreamSieveError):
    """Invalid configuration (schema failure, guardrail violation)."""


class TrainingProhibitedError(StreamSieveError):
    """Attempted training/fine-tuning inside the pipeline (G4 violation)."""


class GovernanceError(StreamSieveError):
    """Governance control violated (e.g., trying to persist raw frames — G2)."""
