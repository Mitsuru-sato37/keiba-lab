from datetime import UTC, datetime

import pytest
from keiba_application.errors import RecommendationNotPersistedError
from keiba_infrastructure.repositories import RecommendationRepository, ResultRepository
from keiba_infrastructure.schema import (
    DataSnapshot,
    FeatureVersion,
    LogicVersion,
    ModelVersion,
    PredictionSnapshot,
    Recommendation,
    Result,
)
from sqlalchemy.orm import Session

NOW = datetime(2022, 1, 1, tzinfo=UTC)


def test_result_cannot_be_persisted_before_recommendation(migrated_session: Session) -> None:
    result_repository = ResultRepository(migrated_session)

    with pytest.raises(RecommendationNotPersistedError):
        result_repository.add(
            Result(
                result_id="result-1",
                race_id="race-1",
                recommendation_id="missing-recommendation",
                payload={"finish": [1, 2, 3]},
                persisted_at=NOW,
            ),
        )


def test_result_is_allowed_after_recommendation_persistence(migrated_session: Session) -> None:
    migrated_session.add_all(
        [
            ModelVersion(
                version_id="model-v1",
                model_name="baseline",
                manifest={},
                created_at=NOW,
            ),
            FeatureVersion(
                version_id="feature-v1",
                feature_name="core",
                manifest={},
                created_at=NOW,
            ),
            LogicVersion(
                version_id="logic-v1",
                logic_id="RECO-001",
                manifest={},
                created_at=NOW,
            ),
            DataSnapshot(
                snapshot_id="snapshot-1",
                as_of_time=NOW,
                data_version="data-v1",
                manifest={},
                created_at=NOW,
            ),
        ],
    )
    migrated_session.flush()
    migrated_session.add(
        PredictionSnapshot(
            prediction_snapshot_id="prediction-1",
            race_id="race-1",
            as_of_time=NOW,
            data_snapshot_id="snapshot-1",
            feature_version_id="feature-v1",
            model_version_id="model-v1",
            logic_version_id="logic-v1",
            predictions={},
            created_at=NOW,
        ),
    )
    migrated_session.flush()

    RecommendationRepository(migrated_session).add(
        Recommendation(
            recommendation_id="recommendation-1",
            race_id="race-1",
            decision="SKIP",
            strategy="balanced",
            data_snapshot_id="snapshot-1",
            prediction_snapshot_id="prediction-1",
            feature_version_id="feature-v1",
            model_version_id="model-v1",
            logic_version_id="logic-v1",
            payload={"reason_codes": ["no-value"]},
            persisted_at=NOW,
        ),
    )

    ResultRepository(migrated_session).add(
        Result(
            result_id="result-1",
            race_id="race-1",
            recommendation_id="recommendation-1",
            payload={"finish": [1, 2, 3]},
            persisted_at=NOW,
        ),
    )
    assert migrated_session.get(Result, "result-1") is not None
