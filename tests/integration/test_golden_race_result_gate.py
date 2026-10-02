from datetime import UTC, datetime

import pytest
from keiba_application.errors import RecommendationNotPersistedError, ResultNotAvailableError
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


def add_dependencies(session: Session) -> None:
    session.add_all(
        [
            ModelVersion(version_id="model-1", model_name="golden", manifest={}, created_at=NOW),
            FeatureVersion(
                version_id="feature-1", feature_name="golden", manifest={}, created_at=NOW
            ),
            LogicVersion(version_id="logic-1", logic_id="TRACE-001", manifest={}, created_at=NOW),
            DataSnapshot(
                snapshot_id="data-1",
                as_of_time=NOW,
                data_version="golden-v1",
                manifest={},
                created_at=NOW,
            ),
        ],
    )
    session.flush()
    session.add(
        PredictionSnapshot(
            prediction_snapshot_id="prediction-1",
            race_id="race-1",
            as_of_time=NOW,
            data_snapshot_id="data-1",
            feature_version_id="feature-1",
            model_version_id="model-1",
            logic_version_id="logic-1",
            predictions={"horse-1": 1.0},
            created_at=NOW,
        ),
    )
    session.flush()


def recommendation() -> Recommendation:
    return Recommendation(
        recommendation_id="recommendation-1",
        race_id="race-1",
        decision="BUY",
        strategy="golden",
        data_snapshot_id="data-1",
        prediction_snapshot_id="prediction-1",
        feature_version_id="feature-1",
        model_version_id="model-1",
        logic_version_id="logic-1",
        payload={"allocation_yen": 300},
        persisted_at=NOW,
    )


def test_result_reveal_is_denied_before_recommendation(migrated_session: Session) -> None:
    with pytest.raises(RecommendationNotPersistedError):
        ResultRepository(migrated_session).reveal(race_id="race-1", recommendation_id="missing")


def test_result_reveal_requires_result_after_recommendation(migrated_session: Session) -> None:
    add_dependencies(migrated_session)
    RecommendationRepository(migrated_session).add(recommendation())

    with pytest.raises(ResultNotAvailableError):
        ResultRepository(migrated_session).reveal(
            race_id="race-1", recommendation_id="recommendation-1"
        )

    ResultRepository(migrated_session).add(
        Result(
            result_id="result-1",
            race_id="race-1",
            recommendation_id="recommendation-1",
            payload={"winner": "horse-1", "payouts": {"win": 280}},
            persisted_at=NOW,
        ),
    )
    revealed = ResultRepository(migrated_session).reveal(
        race_id="race-1", recommendation_id="recommendation-1"
    )
    assert revealed.result_id == "result-1"
