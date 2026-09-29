from datetime import datetime, timedelta
from decimal import Decimal
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field, field_validator


def require_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("datetime must be timezone-aware")
    if value.utcoffset() != timedelta(0):
        raise ValueError("datetime must be UTC")
    return value


class ProviderRecord(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    provider: str = Field(min_length=1)
    provider_key: str = Field(min_length=1)
    received_timestamp: datetime
    effective_from: datetime
    snapshot_id: str = Field(min_length=1)
    payload_checksum: str = Field(min_length=1)

    @field_validator("received_timestamp", "effective_from")
    @classmethod
    def validate_utc(cls, value: datetime) -> datetime:
        return require_utc(value)


class RunnerRecord(ProviderRecord):
    horse_id: str = Field(min_length=1)
    horse_number: int = Field(ge=1)


class RaceRecord(ProviderRecord):
    race_id: str = Field(min_length=1)
    scheduled_post_time: datetime
    runners: tuple[RunnerRecord, ...] = Field(min_length=1)

    @field_validator("scheduled_post_time")
    @classmethod
    def validate_post_time(cls, value: datetime) -> datetime:
        return require_utc(value)


class OddsRecord(ProviderRecord):
    race_id: str = Field(min_length=1)
    horse_id: str = Field(min_length=1)
    current_odds: Decimal = Field(gt=0)


class RaceProvider(Protocol):
    def list_races(self, as_of_time: datetime) -> tuple[RaceRecord, ...]: ...

    def get_race(self, race_id: str, as_of_time: datetime) -> RaceRecord | None: ...

    def get_odds(self, race_id: str, as_of_time: datetime) -> tuple[OddsRecord, ...]: ...
