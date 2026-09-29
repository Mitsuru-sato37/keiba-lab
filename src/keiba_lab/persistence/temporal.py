from datetime import datetime, timedelta

from pydantic import BaseModel, ConfigDict, field_validator


def require_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("datetime must be timezone-aware")
    if value.utcoffset() != timedelta(0):
        raise ValueError("datetime must be UTC")
    return value


class ObservationRecord(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    observation_id: str
    provider: str
    provider_key: str
    received_timestamp: datetime
    effective_from: datetime
    effective_to: datetime | None = None
    batch_status: str

    @field_validator("received_timestamp", "effective_from", "effective_to")
    @classmethod
    def validate_timestamp(cls, value: datetime | None) -> datetime | None:
        return None if value is None else require_utc(value)


class InMemoryObservationRepository:
    def __init__(self) -> None:
        self._rows: dict[str, ObservationRecord] = {}

    def append(self, record: ObservationRecord) -> None:
        if record.observation_id in self._rows:
            raise ValueError("append-only repository rejects duplicate observation")
        self._rows[record.observation_id] = record

    def eligible(self, provider_key: str, as_of_time: datetime) -> tuple[ObservationRecord, ...]:
        as_of = require_utc(as_of_time)
        return tuple(
            row
            for row in self._rows.values()
            if row.provider_key == provider_key
            and row.batch_status == "promoted"
            and row.received_timestamp <= as_of
            and row.effective_from <= as_of
            and (row.effective_to is None or row.effective_to > as_of)
        )
