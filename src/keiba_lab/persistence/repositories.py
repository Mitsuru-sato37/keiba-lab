from copy import deepcopy
from types import MappingProxyType
from typing import Any


class AppendOnlyRepository:
    """Small in-memory append-only seam used by deterministic Phase 1 services."""

    def __init__(self) -> None:
        self._records: dict[str, MappingProxyType[str, Any]] = {}

    def append(self, artifact_id: str, payload: dict[str, Any]) -> None:
        if artifact_id in self._records:
            raise ValueError("append-only repository rejects duplicate artifact")
        self._records[artifact_id] = MappingProxyType(deepcopy(payload))

    def get(self, artifact_id: str) -> MappingProxyType[str, Any]:
        return self._records[artifact_id]

    def all(self) -> tuple[MappingProxyType[str, Any], ...]:
        return tuple(self._records.values())
