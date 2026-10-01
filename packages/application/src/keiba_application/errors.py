class AppendOnlyViolationError(RuntimeError):
    """Raised when an immutable artifact is asked to change or be deleted."""


class RecommendationNotPersistedError(RuntimeError):
    """Raised when a result is accessed before its recommendation exists."""


class BatchConflictError(RuntimeError):
    """Raised when one batch ID is reused for different content or metadata."""


class TemporalLeakError(ValueError):
    """Raised when a snapshot input was not knowable at its as-of time."""


class OddsLeakError(ValueError):
    """Raised when current-race odds enter the ability feature path."""


class TrainingLeakError(ValueError):
    """Raised when a training manifest contains data from its test period."""


class PredictionInvariantError(ValueError):
    """Raised when a prediction artifact violates probability or lineage rules."""
