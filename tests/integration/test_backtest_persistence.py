from datetime import UTC, datetime
from typing import Any

import pytest
from keiba_application.errors import AppendOnlyViolationError
from keiba_infrastructure.repositories import BacktestPersistenceRepository
from keiba_infrastructure.schema import (
    BacktestArtifact,
    BacktestFold,
    BacktestGuardResult,
    BacktestRun,
)
from sqlalchemy import delete, update
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

NOW = datetime(2022, 1, 1, tzinfo=UTC)


def records() -> tuple[BacktestRun, BacktestFold, BacktestGuardResult, BacktestArtifact]:
    run = BacktestRun(
        run_id="run-1",
        status="succeeded",
        manifest={"run_id": "run-1", "seed": 7},
        manifest_checksum="m" * 64,
        started_at=NOW,
        completed_at=NOW,
        created_at=NOW,
    )
    fold = BacktestFold(
        fold_id="fold-2022",
        run_id="run-1",
        test_year=2022,
        training_years=[2019, 2020, 2021],
        status="succeeded",
        manifest={"test_year": 2022},
        manifest_checksum="f" * 64,
        created_at=NOW,
    )
    guard = BacktestGuardResult(
        guard_result_id="guard-1",
        run_id="run-1",
        fold_id="fold-2022",
        guard_id="LEAK-001",
        guard_version="LEAK-001-v1",
        status="pass",
        checked_input_ids=["observation-1"],
        details={"as_of": NOW.isoformat()},
        created_at=NOW,
    )
    artifact = BacktestArtifact(
        artifact_id="artifact-1",
        run_id="run-1",
        fold_id="fold-2022",
        artifact_kind="prediction",
        artifact_ref_id="prediction-1",
        manifest={"prediction_snapshot_id": "prediction-1"},
        created_at=NOW,
    )
    return run, fold, guard, artifact


def test_backtest_records_persist_lineage_and_manifests(migrated_session: Session) -> None:
    run, fold, guard, artifact = records()
    repository = BacktestPersistenceRepository(migrated_session)

    repository.add_run(run)
    repository.add_fold(fold)
    repository.add_guard_result(guard)
    repository.add_artifact(artifact)

    assert migrated_session.get(BacktestRun, "run-1") is run
    persisted_fold = migrated_session.get(BacktestFold, "fold-2022")
    persisted_guard = migrated_session.get(BacktestGuardResult, "guard-1")
    persisted_artifact = migrated_session.get(BacktestArtifact, "artifact-1")
    assert persisted_fold is not None
    assert persisted_guard is not None
    assert persisted_artifact is not None
    assert persisted_fold.run_id == "run-1"
    assert persisted_guard.guard_id == "LEAK-001"
    assert persisted_artifact.artifact_ref_id == "prediction-1"


@pytest.mark.parametrize(
    "operation",
    [
        "update_run",
        "delete_run",
        "update_fold",
        "delete_fold",
        "update_guard_result",
        "delete_guard_result",
        "update_artifact",
        "delete_artifact",
    ],
)
def test_repository_rejects_backtest_updates_and_deletes(
    migrated_session: Session,
    operation: str,
) -> None:
    repository = BacktestPersistenceRepository(migrated_session)

    with pytest.raises(AppendOnlyViolationError):
        getattr(repository, operation)("record-1")


@pytest.mark.parametrize(
    ("model", "id_attribute", "identifier", "field", "value"),
    [
        (BacktestRun, "run_id", "run-1", "status", "invalid"),
        (BacktestFold, "fold_id", "fold-2022", "status", "invalid"),
        (BacktestGuardResult, "guard_result_id", "guard-1", "status", "fail"),
        (BacktestArtifact, "artifact_id", "artifact-1", "artifact_kind", "result"),
    ],
)
def test_database_triggers_reject_backtest_updates(
    migrated_session: Session,
    model: Any,
    id_attribute: str,
    identifier: str,
    field: str,
    value: str,
) -> None:
    run, fold, guard, artifact = records()
    repository = BacktestPersistenceRepository(migrated_session)
    repository.add_run(run)
    repository.add_fold(fold)
    repository.add_guard_result(guard)
    repository.add_artifact(artifact)

    with pytest.raises(DBAPIError, match="append-only"):
        migrated_session.execute(
            update(model)
            .where(getattr(model, id_attribute) == identifier)
            .values({field: value}),
        )


def test_database_triggers_reject_backtest_deletes(migrated_session: Session) -> None:
    run, fold, guard, artifact = records()
    repository = BacktestPersistenceRepository(migrated_session)
    repository.add_run(run)
    repository.add_fold(fold)
    repository.add_guard_result(guard)
    repository.add_artifact(artifact)

    with pytest.raises(DBAPIError, match="append-only"):
        migrated_session.execute(
            delete(BacktestArtifact).where(BacktestArtifact.artifact_id == "artifact-1"),
        )
