import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime

from keiba_application.errors import BatchConflictError
from keiba_application.ports import ObservationBatch
from sqlalchemy.orm import Session

from .collector_contract import batch_to_json
from .repositories import TemporalObservationRepository
from .schema import IngestionBatch, RawObservation


@dataclass(frozen=True, slots=True)
class BatchPromotionResult:
    batch_id: str
    inserted: bool


def _content_checksum(batch: ObservationBatch) -> str:
    return hashlib.sha256(batch_to_json(batch).encode("utf-8")).hexdigest()


class BatchPromotionRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def promote(self, batch: ObservationBatch) -> BatchPromotionResult:
        content_checksum = _content_checksum(batch)
        existing = self._session.get(IngestionBatch, batch.batch_id)
        if existing is not None:
            if (
                existing.provider == batch.provider
                and existing.provider_version == batch.provider_version
                and existing.content_checksum == content_checksum
                and existing.record_count == len(batch.records)
            ):
                return BatchPromotionResult(batch_id=batch.batch_id, inserted=False)
            raise BatchConflictError(f"batch_id {batch.batch_id} conflicts with existing content")

        for record in batch.records:
            existing_record = self._session.get(RawObservation, record.record_id)
            if existing_record is not None:
                raise BatchConflictError(
                    f"record_id {record.record_id} already belongs to another batch",
                )

        self._session.add(
            IngestionBatch(
                batch_id=batch.batch_id,
                provider=batch.provider,
                provider_version=batch.provider_version,
                collected_at=batch.collected_at.value,
                content_checksum=content_checksum,
                record_count=len(batch.records),
                status="PROMOTED",
                created_at=datetime.now(UTC),
            ),
        )
        repository = TemporalObservationRepository(self._session)
        for record in batch.records:
            repository.add(record, ingestion_batch_id=batch.batch_id)
        self._session.flush()
        return BatchPromotionResult(batch_id=batch.batch_id, inserted=True)
