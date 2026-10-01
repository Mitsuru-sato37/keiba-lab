class AppendOnlyViolationError(RuntimeError):
    """Raised when an immutable artifact is asked to change or be deleted."""


class RecommendationNotPersistedError(RuntimeError):
    """Raised when a result is accessed before its recommendation exists."""


class BatchConflictError(RuntimeError):
    """Raised when one batch ID is reused for different content or metadata."""
