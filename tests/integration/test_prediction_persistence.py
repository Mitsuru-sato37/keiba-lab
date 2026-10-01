from datetime import UTC, datetime

import pytest
from keiba_application.errors import AppendOnlyViolationError
from keiba_application.predictions import PredictionSnapshot, RunnerPrediction
from keiba_domain.time_values import UtcInstant
from keiba_infrastructure.predictions import PredictionSnapshotRepository
from keiba_infrastructure.schema import (
    DataSnapshot,
    FeatureVersion,
    LogicVersion,
    ModelVersion,
)
from keiba_infrastructure.schema import (
    PredictionSnapshot as StoredPredictionSnapshot,
)
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


def as_of_time() -> UtcInstant:
    return UtcInstant.from_datetime(datetime(2022, 1, 1, 10, tzinfo=UTC))


def prediction(
    *,
    prediction_snapshot_id: str = "prediction-1",
    model_version_id: str = "baseline-gate-v1",
) -> PredictionSnapshot:
    return PredictionSnapshot(
        prediction_snapshot_id=prediction_snapshot_id,
        race_id="race-1",
        as_of_time=as_of_time(),
        data_snapshot_id="snapshot-1",
        feature_version_id="core-feature-v1",
        model_version_id=model_version_id,
        logic_version_id="MODEL-BASE-001-v1",
        training_manifest_id="training-2022-v1",
        model_manifest_checksum="a" * 64,
        calibration_version_id=None,
        predictions=(
            RunnerPrediction(
                runner_id="runner-1",
                raw_win_probability=0.6,
                win_probability=0.6,
                raw_top2_probability=0.8,
                top2_probability=0.8,
                raw_top3_probability=1.0,
                top3_probability=1.0,
                ranking_score=0.6,
                uncertainty=0.4,
                disagreement=0.0,
            ),
            RunnerPrediction(
                runner_id="runner-2",
                raw_win_probability=0.4,
                win_probability=0.4,
                raw_top2_probability=0.6,
                top2_probability=0.6,
                raw_top3_probability=1.0,
                top3_probability=1.0,
                ranking_score=0.4,
                uncertainty=0.5,
                disagreement=0.0,
            ),
        ),
    )


def add_versions(session: Session, *, include_second_model: bool = False) -> None:
    session.add(
        DataSnapshot(
            snapshot_id="snapshot-1",
            as_of_time=as_of_time().value,
            data_version="race-snapshot-v1",
            manifest={"race_id": "race-1"},
            created_at=datetime.now(UTC),
        ),
    )
    session.add(
        FeatureVersion(
            version_id="core-feature-v1",
            feature_name="core-feature-v1",
            manifest={"logic_id": "FEAT-001"},
            created_at=datetime.now(UTC),
        ),
    )
    session.add(
        LogicVersion(
            version_id="MODEL-BASE-001-v1",
            logic_id="MODEL-BASE-001",
            manifest={"feature_version": "core-feature-v1"},
            created_at=datetime.now(UTC),
        ),
    )
    model_versions = ["baseline-gate-v1"]
    if include_second_model:
        model_versions.append("baseline-gate-v2")
    for model_version_id in model_versions:
        session.add(
            ModelVersion(
                version_id=model_version_id,
                model_name="gate-strength-baseline",
                manifest={"training_manifest_id": "training-2022-v1"},
                created_at=datetime.now(UTC),
            ),
        )
    session.flush()


def test_prediction_persistence_retains_lineage(migrated_session: Session) -> None:
    add_versions(migrated_session)

    PredictionSnapshotRepository(migrated_session).add(prediction())

    stored = migrated_session.get(StoredPredictionSnapshot, "prediction-1")
    assert stored is not None
    assert stored.race_id == "race-1"
    assert stored.data_snapshot_id == "snapshot-1"
    assert stored.feature_version_id == "core-feature-v1"
    assert stored.model_version_id == "baseline-gate-v1"
    assert stored.logic_version_id == "MODEL-BASE-001-v1"
    assert stored.predictions["training_manifest_id"] == "training-2022-v1"
    assert stored.predictions["model_manifest_checksum"] == "a" * 64
    assert stored.predictions["runners"][0]["win_probability"] == 0.6
    assert stored.predictions["runners"][0]["raw_win_probability"] == 0.6


def test_prediction_repository_is_append_only(migrated_session: Session) -> None:
    add_versions(migrated_session)
    repository = PredictionSnapshotRepository(migrated_session)
    artifact = prediction()
    repository.add(artifact)

    with pytest.raises(AppendOnlyViolationError):
        repository.update(artifact)
    with pytest.raises(AppendOnlyViolationError):
        repository.delete(artifact)


def test_prediction_repository_keeps_model_versions_separate(
    migrated_session: Session,
) -> None:
    add_versions(migrated_session, include_second_model=True)
    repository = PredictionSnapshotRepository(migrated_session)

    repository.add(prediction())
    repository.add(
        prediction(
            prediction_snapshot_id="prediction-2",
            model_version_id="baseline-gate-v2",
        ),
    )

    count = migrated_session.scalar(
        select(func.count()).select_from(StoredPredictionSnapshot),
    )
    assert count == 2


def test_repeated_identical_prediction_id_is_rejected(migrated_session: Session) -> None:
    add_versions(migrated_session)
    repository = PredictionSnapshotRepository(migrated_session)
    artifact = prediction()
    repository.add(artifact)

    with pytest.raises(IntegrityError):
        repository.add(artifact)
    migrated_session.rollback()
