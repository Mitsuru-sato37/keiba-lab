from datetime import UTC, datetime

from keiba_application.ports import ObservationRecord
from keiba_domain.time_values import UtcInstant
from keiba_infrastructure.repositories import TemporalObservationRepository
from sqlalchemy.orm import Session


def instant(hour: int) -> UtcInstant:
    return UtcInstant.from_datetime(datetime(2022, 1, 1, hour, tzinfo=UTC))


def observation(
    record_id: str,
    *,
    received_hour: int,
    effective_hour: int,
) -> ObservationRecord:
    return ObservationRecord(
        record_id=record_id,
        source="fixture",
        source_version="v1",
        source_timestamp=instant(effective_hour),
        received_timestamp=instant(received_hour),
        effective_from=instant(effective_hour),
        payload={"record_id": record_id},
    )


def test_eligible_as_of_excludes_future_received_and_effective_records(
    migrated_session: Session,
) -> None:
    repository = TemporalObservationRepository(migrated_session)
    repository.add(observation("eligible", received_hour=9, effective_hour=9))
    repository.add(observation("received-future", received_hour=11, effective_hour=9))
    repository.add(observation("effective-future", received_hour=9, effective_hour=11))

    result = repository.eligible_as_of(instant(10))

    assert [record.record_id for record in result] == ["eligible"]


def test_eligible_as_of_excludes_record_after_effective_to(
    migrated_session: Session,
) -> None:
    repository = TemporalObservationRepository(migrated_session)
    repository.add(
        observation("superseded", received_hour=8, effective_hour=8),
        effective_to=instant(10),
    )

    assert repository.eligible_as_of(instant(9))[0].record_id == "superseded"
    assert repository.eligible_as_of(instant(10)) == ()
