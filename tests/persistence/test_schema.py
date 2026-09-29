from datetime import UTC, datetime

import pytest

from keiba_lab.persistence.repositories import AppendOnlyRepository
from keiba_lab.persistence.schema import metadata
from keiba_lab.persistence.temporal import InMemoryObservationRepository, ObservationRecord


def test_schema_keeps_required_lifecycle_tables() -> None:
    required = {
        "raw_observation",
        "race_snapshot",
        "horse_prediction",
        "recommendation",
        "backtest_run",
        "race",
        "runner",
        "odds_snapshot",
        "prediction_snapshot",
        "logic_version",
        "policy_version",
    }
    assert required <= set(metadata.tables)


def test_temporal_repository_requires_as_of_time_and_filters_superseded_rows() -> None:
    repo = InMemoryObservationRepository()
    first = ObservationRecord(
        observation_id="O1",
        provider="FIXTURE",
        provider_key="R1",
        received_timestamp=datetime(2022, 1, 1, 0, tzinfo=UTC),
        effective_from=datetime(2022, 1, 1, 1, tzinfo=UTC),
        effective_to=datetime(2022, 1, 1, 2, tzinfo=UTC),
        batch_status="promoted",
    )
    second = first.model_copy(
        update={
            "observation_id": "O2",
            "effective_from": datetime(2022, 1, 1, 2, tzinfo=UTC),
            "effective_to": None,
        }
    )
    repo.append(first)
    repo.append(second)
    assert [
        row.observation_id for row in repo.eligible("R1", datetime(2022, 1, 1, 1, 30, tzinfo=UTC))
    ] == ["O1"]
    assert [
        row.observation_id for row in repo.eligible("R1", datetime(2022, 1, 1, 2, tzinfo=UTC))
    ] == ["O2"]


def test_temporal_repository_rejects_naive_as_of_time_and_duplicate_append() -> None:
    repo = InMemoryObservationRepository()
    row = ObservationRecord(
        observation_id="O1",
        provider="FIXTURE",
        provider_key="R1",
        received_timestamp=datetime(2022, 1, 1, tzinfo=UTC),
        effective_from=datetime(2022, 1, 1, tzinfo=UTC),
        batch_status="promoted",
    )
    repo.append(row)
    with pytest.raises(ValueError, match="timezone-aware"):
        repo.eligible("R1", datetime(2022, 1, 1))
    with pytest.raises(ValueError, match="append-only"):
        repo.append(row)


def test_artifact_repository_is_append_only_and_returns_immutable_payload() -> None:
    repo = AppendOnlyRepository()
    payload = {"snapshot_id": "S1", "logic_version": "LOGIC:v1"}
    repo.append("S1", payload)
    payload["logic_version"] = "LOGIC:v2"
    assert repo.get("S1")["logic_version"] == "LOGIC:v1"
    with pytest.raises(ValueError, match="append-only"):
        repo.append("S1", {})
