from dataclasses import replace

import pytest
from keiba_application.errors import BatchConflictError
from keiba_infrastructure.batch_promotion import (
    BatchPromotionRepository,
)
from keiba_infrastructure.fixtures import DeterministicFixtureProvider
from keiba_infrastructure.schema import IngestionBatch, RawObservation
from sqlalchemy import func, select
from sqlalchemy.orm import Session


def test_promoting_the_same_batch_twice_is_idempotent(migrated_session: Session) -> None:
    batch = DeterministicFixtureProvider(seed=7, fixture_version="v1").collect()
    repository = BatchPromotionRepository(migrated_session)

    first = repository.promote(batch)
    second = repository.promote(batch)

    assert first.inserted is True
    assert second.inserted is False
    assert migrated_session.scalar(select(func.count()).select_from(IngestionBatch)) == 1
    assert migrated_session.scalar(select(func.count()).select_from(RawObservation)) == 3


def test_reusing_a_batch_id_with_different_metadata_fails_closed(
    migrated_session: Session,
) -> None:
    batch = DeterministicFixtureProvider(seed=7, fixture_version="v1").collect()
    repository = BatchPromotionRepository(migrated_session)
    repository.promote(batch)

    conflicting_batch = replace(batch, provider_version="v2")

    with pytest.raises(BatchConflictError, match="batch_id"):
        repository.promote(conflicting_batch)
