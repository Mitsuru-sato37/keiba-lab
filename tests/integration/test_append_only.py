from datetime import UTC, datetime

import pytest
from keiba_application.errors import AppendOnlyViolationError
from keiba_infrastructure.repositories import TemporalObservationRepository
from keiba_infrastructure.schema import RawObservation
from sqlalchemy import update
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session


def test_repository_rejects_update_and_delete(migrated_session: Session) -> None:
    repository = TemporalObservationRepository(migrated_session)

    with pytest.raises(AppendOnlyViolationError):
        repository.update("observation-1")
    with pytest.raises(AppendOnlyViolationError):
        repository.delete("observation-1")


def test_database_trigger_rejects_raw_observation_update(migrated_session: Session) -> None:
    migrated_session.add(
        RawObservation(
            observation_id="observation-1",
            provider="fixture",
            provider_version="v1",
            provider_record_type="observation",
            provider_record_key="observation-1",
            source_timestamp=datetime(2022, 1, 1, tzinfo=UTC),
            received_timestamp=datetime(2022, 1, 1, tzinfo=UTC),
            effective_from=datetime(2022, 1, 1, tzinfo=UTC),
            payload={"value": 1},
            payload_checksum="checksum",
            ingestion_batch_id="batch-1",
            created_at=datetime(2022, 1, 1, tzinfo=UTC),
        ),
    )
    migrated_session.flush()

    with pytest.raises(DBAPIError, match="append-only"):
        migrated_session.execute(
            update(RawObservation)
            .where(RawObservation.observation_id == "observation-1")
            .values(provider="changed"),
        )
