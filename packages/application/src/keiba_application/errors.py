class AppendOnlyViolationError(RuntimeError):
    """Raised when an immutable artifact is asked to change or be deleted."""


class RecommendationNotPersistedError(RuntimeError):
    """Raised when a result is accessed before its recommendation exists."""
