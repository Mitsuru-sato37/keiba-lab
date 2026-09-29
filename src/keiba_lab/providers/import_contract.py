from datetime import datetime, timedelta
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


def require_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("datetime must be timezone-aware")
    if value.utcoffset() != timedelta(0):
        raise ValueError("datetime must be UTC")
    return value


class ImportRecord(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    provider_key: str = Field(min_length=1)
    payload: str
    checksum: str = Field(min_length=1)


class ImportBatch(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    provider: str = Field(min_length=1)
    contract_version: str = Field(min_length=1)
    batch_id: str = Field(min_length=1)
    received_at: datetime
    records: tuple[ImportRecord, ...] = Field(min_length=1)

    @field_validator("received_at")
    @classmethod
    def validate_received_at(cls, value: datetime) -> datetime:
        return require_utc(value)


class ImportBatchStore:
    def __init__(self) -> None:
        self._batches: dict[
            str, tuple[ImportBatch, Literal["staged", "promoted", "failed"], str | None]
        ] = {}

    def stage(self, batch: ImportBatch) -> None:
        existing = self._batches.get(batch.batch_id)
        if existing is not None:
            if existing[0] != batch:
                raise ValueError("import batch is immutable")
            return
        self._batches[batch.batch_id] = (batch, "staged", None)

    def promote(self, batch_id: str) -> bool:
        batch, status, error = self._batches[batch_id]
        if status == "promoted":
            return False
        if status == "failed":
            return False
        self._batches[batch_id] = (batch, "promoted", error)
        return True

    def fail(self, batch_id: str, reason: str) -> None:
        batch, _, _ = self._batches[batch_id]
        self._batches[batch_id] = (batch, "failed", reason)

    def eligible(self, batch_id: str) -> tuple[ImportRecord, ...]:
        batch, status, _ = self._batches[batch_id]
        return batch.records if status == "promoted" else ()
