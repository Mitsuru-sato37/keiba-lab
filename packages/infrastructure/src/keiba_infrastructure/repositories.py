import hashlib
import json
from datetime import UTC, datetime
from typing import Any

from keiba_application.errors import AppendOnlyViolationError, RecommendationNotPersistedError
from keiba_application.ports import ObservationRecord
from keiba_domain.time_values import UtcInstant
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from .schema import RawObservation, Recommendation, Result


def _utc_datetime(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _utc_instant(value: datetime) -> UtcInstant:
    return UtcInstant.from_datetime(_utc_datetime(value))


def _payload_checksum(payload: dict[str, Any]) -> str:
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


class TemporalObservationRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(
        self,
        record: ObservationRecord,
        *,
        effective_to: UtcInstant | None = None,
    ) -> None:
        payload = dict(record.payload)
        self._session.add(
            RawObservation(
                observation_id=record.record_id,
                provider=record.source,
                provider_version=record.source_version,
                provider_record_type="observation",
                provider_record_key=record.record_id,
                source_timestamp=record.source_timestamp.value,
                received_timestamp=record.received_timestamp.value,
                effective_from=record.effective_from.value,
                effective_to=effective_to.value if effective_to else None,
                payload=payload,
                payload_checksum=_payload_checksum(payload),
                ingestion_batch_id=f"fixture:{record.source_version}",
                created_at=datetime.now(UTC),
            ),
        )
        self._session.flush()

    def eligible_as_of(self, as_of_time: UtcInstant) -> tuple[ObservationRecord, ...]:
        cutoff = as_of_time.value
        statement = (
            select(RawObservation)
            .where(
                and_(
                    RawObservation.received_timestamp <= cutoff,
                    RawObservation.effective_from <= cutoff,
                    or_(
                        RawObservation.effective_to.is_(None), RawObservation.effective_to > cutoff
                    ),
                ),
            )
            .order_by(RawObservation.observation_id)
        )
        rows = self._session.scalars(statement).all()
        return tuple(
            ObservationRecord(
                record_id=row.observation_id,
                source=row.provider,
                source_version=row.provider_version,
                source_timestamp=_utc_instant(row.source_timestamp),
                received_timestamp=_utc_instant(row.received_timestamp),
                effective_from=_utc_instant(row.effective_from),
                payload=row.payload,
            )
            for row in rows
        )

    def update(self, *_: object, **__: object) -> None:
        raise AppendOnlyViolationError("raw_observations is append-only")

    def delete(self, *_: object, **__: object) -> None:
        raise AppendOnlyViolationError("raw_observations is append-only")


class RecommendationRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, recommendation: Recommendation) -> None:
        self._session.add(recommendation)
        self._session.flush()

    def update(self, *_: object, **__: object) -> None:
        raise AppendOnlyViolationError("recommendations is append-only")

    def delete(self, *_: object, **__: object) -> None:
        raise AppendOnlyViolationError("recommendations is append-only")


class ResultRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, result: Result) -> None:
        recommendation = self._session.get(Recommendation, result.recommendation_id)
        if recommendation is None:
            raise RecommendationNotPersistedError(
                f"recommendation {result.recommendation_id} is not persisted",
            )
        if recommendation.race_id != result.race_id:
            raise ValueError("result race_id must match recommendation race_id")
        self._session.add(result)
        self._session.flush()
