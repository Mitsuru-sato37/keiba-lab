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


class ObservationProvider(Protocol):
    def observations(self) -> tuple[ObservationRecord, ...]: ...
