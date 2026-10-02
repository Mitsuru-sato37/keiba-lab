from datetime import UTC, datetime

import pytest
from keiba_application.errors import AppendOnlyViolationError
from keiba_application.golden_race import Lineage, StageArtifact, StageId
from keiba_domain.time_values import UtcInstant
from keiba_infrastructure.repositories import GoldenRacePersistenceRepository
from keiba_infrastructure.schema import CalculationArtifact, LogicTrace
from sqlalchemy import delete, update
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

NOW = datetime(2022, 1, 1, tzinfo=UTC)


def artifact() -> StageArtifact:
    return StageArtifact.create(
        artifact_id="run-1:race-1:prediction",
        run_id="run-1",
        race_id="race-1",
        stage=StageId.PREDICTION,
        output={"win_probabilities": {"horse-1": 1.0}},
        lineage=Lineage(
            data_snapshot_id="data-1",
            feature_version_id="feature-1",
            model_version_id="model-1",
            logic_version_id="logic-1",
            input_ids=("feature-1",),
        ),
        calculated_at=UtcInstant.from_datetime(NOW),
    )


def test_golden_artifact_and_trace_persist_lineage(migrated_session: Session) -> None:
    repository = GoldenRacePersistenceRepository(migrated_session)

    repository.add_stage_artifact(artifact(), stage_order=3)

    stored_artifact = migrated_session.get(CalculationArtifact, "run-1:race-1:prediction")
    trace = migrated_session.get(LogicTrace, "trace:run-1:race-1:prediction")
    assert stored_artifact is not None
    assert trace is not None
    assert stored_artifact.checksum == artifact().checksum
    assert trace.stage == "prediction"
    assert trace.stage_order == 3
    assert trace.input_ids == ["feature-1"]
    assert trace.logic_version_id == "logic-1"


@pytest.mark.parametrize("operation", ["update_stage_artifact", "delete_stage_artifact"])
def test_golden_repository_rejects_updates_and_deletes(
    migrated_session: Session,
    operation: str,
) -> None:
    repository = GoldenRacePersistenceRepository(migrated_session)

    with pytest.raises(AppendOnlyViolationError):
        getattr(repository, operation)("artifact-1")


def test_database_trigger_rejects_golden_artifact_update_and_delete(
    migrated_session: Session,
) -> None:
    repository = GoldenRacePersistenceRepository(migrated_session)
    repository.add_stage_artifact(artifact(), stage_order=3)

    with pytest.raises(DBAPIError, match="append-only"):
        migrated_session.execute(
            update(CalculationArtifact)
            .where(CalculationArtifact.artifact_id == "run-1:race-1:prediction")
            .values(stage="result"),
        )
    migrated_session.rollback()
    repository.add_stage_artifact(artifact(), stage_order=3)

    with pytest.raises(DBAPIError, match="append-only"):
        migrated_session.execute(
            delete(CalculationArtifact).where(
                CalculationArtifact.artifact_id == "run-1:race-1:prediction",
            ),
        )
