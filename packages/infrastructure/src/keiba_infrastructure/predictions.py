from dataclasses import asdict
from datetime import UTC, datetime
from typing import Any

from keiba_application.errors import AppendOnlyViolationError
from keiba_application.predictions import PredictionSnapshot as PredictionArtifact
from sqlalchemy.orm import Session

from .schema import PredictionSnapshot


class PredictionSnapshotRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, artifact: PredictionArtifact) -> None:
        payload: dict[str, Any] = {
            "training_manifest_id": artifact.training_manifest_id,
            "model_manifest_checksum": artifact.model_manifest_checksum,
            "calibration_version_id": artifact.calibration_version_id,
            "runners": [asdict(prediction) for prediction in artifact.predictions],
        }
        self._session.add(
            PredictionSnapshot(
                prediction_snapshot_id=artifact.prediction_snapshot_id,
                race_id=artifact.race_id,
                as_of_time=artifact.as_of_time.value,
                data_snapshot_id=artifact.data_snapshot_id,
                feature_version_id=artifact.feature_version_id,
                model_version_id=artifact.model_version_id,
                logic_version_id=artifact.logic_version_id,
                predictions=payload,
                created_at=datetime.now(UTC),
            ),
        )
        self._session.flush()

    def update(self, *_: object, **__: object) -> None:
        raise AppendOnlyViolationError("prediction_snapshots is append-only")

    def delete(self, *_: object, **__: object) -> None:
        raise AppendOnlyViolationError("prediction_snapshots is append-only")
