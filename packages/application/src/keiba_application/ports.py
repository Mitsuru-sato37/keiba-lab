from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol

from keiba_domain.time_values import UtcInstant


@dataclass(frozen=True, slots=True)
class ObservationRecord:
    record_id: str
    source: str
    source_version: str
    source_timestamp: UtcInstant
    received_timestamp: UtcInstant
    effective_from: UtcInstant
    payload: Mapping[str, object]
    provider_record_type: str = "observation"
    provider_record_key: str | None = None
    effective_to: UtcInstant | None = None

    def __post_init__(self) -> None:
        if self.provider_record_key is None:
            object.__setattr__(self, "provider_record_key", self.record_id)


@dataclass(frozen=True, slots=True)
class ObservationBatch:
    batch_id: str
    provider: str
    provider_version: str
    collected_at: UtcInstant
    records: tuple[ObservationRecord, ...]


class ObservationProvider(Protocol):
    def collect(self) -> ObservationBatch: ...
