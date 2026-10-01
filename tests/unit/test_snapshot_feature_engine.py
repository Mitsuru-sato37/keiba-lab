from dataclasses import replace
from datetime import UTC, datetime

import pytest
from keiba_application.errors import OddsLeakError, TemporalLeakError
from keiba_application.ports import ObservationRecord
from keiba_domain.time_values import UtcInstant
from keiba_infrastructure.snapshot_feature import (
    CoreFeatureV1Registry,
    RaceSnapshotBuilder,
)


def instant(hour: int) -> UtcInstant:
    return UtcInstant.from_datetime(datetime(2022, 1, 1, hour, tzinfo=UTC))


def record(
    record_id: str,
    record_type: str,
    payload: dict[str, object],
    *,
    received_hour: int = 10,
    effective_hour: int = 10,
) -> ObservationRecord:
    return ObservationRecord(
        record_id=record_id,
        source="fixture",
        source_version="v1",
        source_timestamp=instant(effective_hour),
        received_timestamp=instant(received_hour),
        effective_from=instant(effective_hour),
        payload=payload,
        provider_record_type=record_type,
        provider_record_key=record_id,
    )


def race_record(**kwargs: object) -> ObservationRecord:
    return record(
        "race-1",
        "race",
        {"race_id": "race-1", "distance_m": 1600, "field_size": 1, "surface": "turf"},
        **kwargs,
    )


def runner_record(**kwargs: object) -> ObservationRecord:
    return record(
        "runner-1",
        "runner",
        {
            "race_id": "race-1",
            "runner_id": "runner-1",
            "gate": 3,
            "horse_number": 5,
            "age": 4,
            "carried_weight_kg": 56.0,
            "days_since_last_race": 21,
        },
        **kwargs,
    )


def test_snapshot_accepts_records_exactly_at_as_of_time() -> None:
    snapshot = RaceSnapshotBuilder().build(
        race_id="race-1",
        as_of_time=instant(10),
        observations=(race_record(), runner_record()),
    )

    assert snapshot.race_id == "race-1"
    assert snapshot.as_of_time == instant(10)
    assert snapshot.observation_ids == ("race-1", "runner-1")
    assert snapshot.runner_ids == ("runner-1",)


def test_snapshot_rejects_a_future_received_observation() -> None:
    with pytest.raises(TemporalLeakError, match="received_timestamp"):
        RaceSnapshotBuilder().build(
            race_id="race-1",
            as_of_time=instant(10),
            observations=(race_record(), runner_record(received_hour=11)),
        )


def test_snapshot_rejects_a_future_effective_observation() -> None:
    with pytest.raises(TemporalLeakError, match="effective_from"):
        RaceSnapshotBuilder().build(
            race_id="race-1",
            as_of_time=instant(10),
            observations=(race_record(), runner_record(effective_hour=11)),
        )


def test_snapshot_rejects_an_observation_superseded_at_as_of_time() -> None:
    superseded = replace(runner_record(), effective_to=instant(10))

    with pytest.raises(TemporalLeakError, match="superseded"):
        RaceSnapshotBuilder().build(
            race_id="race-1",
            as_of_time=instant(10),
            observations=(race_record(), superseded),
        )


def test_snapshot_rejects_current_race_odds_on_ability_path() -> None:
    odds = record(
        "odds-1",
        "odds",
        {"race_id": "race-1", "runner_id": "runner-1", "win_odds": 2.5},
    )

    with pytest.raises(OddsLeakError, match="odds"):
        RaceSnapshotBuilder().build(
            race_id="race-1",
            as_of_time=instant(10),
            observations=(race_record(), runner_record(), odds),
        )


def test_core_feature_v1_returns_lineage_and_values() -> None:
    snapshot = RaceSnapshotBuilder().build(
        race_id="race-1",
        as_of_time=instant(10),
        observations=(race_record(), runner_record()),
        snapshot_id="snapshot-race-1",
    )

    vector = CoreFeatureV1Registry().generate(snapshot, runner_id="runner-1")

    assert vector.feature_version_id == "core-feature-v1"
    assert vector.data_snapshot_id == "snapshot-race-1"
    assert vector.values["race.distance_m"] == 1600
    assert vector.values["race.surface_turf"] is True
    assert vector.values["runner.gate"] == 3
    assert vector.source_observation_ids == ("race-1", "runner-1")
    assert vector.missing_fields == ()


def test_core_feature_v1_reports_missing_fields_explicitly() -> None:
    incomplete_runner = runner_record()
    incomplete_runner = ObservationRecord(
        record_id=incomplete_runner.record_id,
        source=incomplete_runner.source,
        source_version=incomplete_runner.source_version,
        source_timestamp=incomplete_runner.source_timestamp,
        received_timestamp=incomplete_runner.received_timestamp,
        effective_from=incomplete_runner.effective_from,
        payload={"race_id": "race-1", "runner_id": "runner-1", "gate": 3},
        provider_record_type="runner",
        provider_record_key="runner-1",
    )
    snapshot = RaceSnapshotBuilder().build(
        race_id="race-1",
        as_of_time=instant(10),
        observations=(race_record(), incomplete_runner),
    )

    vector = CoreFeatureV1Registry().generate(snapshot, runner_id="runner-1")

    assert vector.values["runner.gate"] == 3
    assert "runner.horse_number" in vector.missing_fields
    assert "runner.days_since_last_race" in vector.missing_fields
