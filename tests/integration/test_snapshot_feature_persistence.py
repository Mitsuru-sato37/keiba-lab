from datetime import UTC, datetime

from keiba_application.ports import ObservationRecord
from keiba_domain.time_values import UtcInstant
from keiba_infrastructure.schema import FeatureVersion, LogicVersion
from keiba_infrastructure.snapshot_feature import (
    CoreFeatureV1Registry,
    DataSnapshotRepository,
    FeatureSnapshotRepository,
    RaceSnapshotBuilder,
)
from sqlalchemy import select
from sqlalchemy.orm import Session


def observation(record_id: str, record_type: str, payload: dict[str, object]) -> ObservationRecord:
    instant = UtcInstant.from_datetime(datetime(2022, 1, 1, 10, tzinfo=UTC))
    return ObservationRecord(
        record_id=record_id,
        source="fixture",
        source_version="v1",
        source_timestamp=instant,
        received_timestamp=instant,
        effective_from=instant,
        payload=payload,
        provider_record_type=record_type,
        provider_record_key=record_id,
    )


def test_snapshot_and_feature_persistence_retain_lineage(migrated_session: Session) -> None:
    observations = (
        observation(
            "race-1",
            "race",
            {"race_id": "race-1", "distance_m": 1600, "field_size": 1, "surface": "turf"},
        ),
        observation(
            "runner-1",
            "runner",
            {"race_id": "race-1", "runner_id": "runner-1", "gate": 3},
        ),
    )
    snapshot = RaceSnapshotBuilder().build(
        race_id="race-1",
        as_of_time=observations[0].received_timestamp,
        observations=observations,
        snapshot_id="snapshot-fixture-race-1",
    )
    feature_vector = CoreFeatureV1Registry().generate(
        snapshot,
        runner_id="runner-1",
    )
    migrated_session.add(
        FeatureVersion(
            version_id="core-feature-v1",
            feature_name="core-feature-v1",
            manifest={"logic_id": "FEAT-001"},
            created_at=datetime.now(UTC),
        ),
    )
    migrated_session.add(
        LogicVersion(
            version_id="FEAT-001-v1",
            logic_id="FEAT-001",
            manifest={"feature_version": "core-feature-v1"},
            created_at=datetime.now(UTC),
        ),
    )

    DataSnapshotRepository(migrated_session).add(snapshot)
    FeatureSnapshotRepository(migrated_session).add(feature_vector)

    stored = migrated_session.execute(
        select(FeatureVersion).where(FeatureVersion.version_id == "core-feature-v1"),
    ).scalar_one()
    assert stored.feature_name == "core-feature-v1"
