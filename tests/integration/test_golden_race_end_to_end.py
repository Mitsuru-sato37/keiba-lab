from datetime import UTC, datetime
from pathlib import Path

import pytest
from keiba_application.errors import ResultNotAvailableError
from keiba_application.golden_race import (
    GoldenRacePipeline,
    PipelineConfig,
    load_golden_race_fixture,
)
from keiba_infrastructure.repositories import (
    GoldenRacePersistenceRepository,
    ResultRepository,
)
from keiba_infrastructure.schema import CalculationArtifact, Evaluation, LogicTrace, Result
from sqlalchemy.orm import Session

NOW = datetime(2022, 1, 1, tzinfo=UTC)
FIXTURE_PATH = Path("fixtures/golden-race/fixture.json")


def config() -> PipelineConfig:
    return PipelineConfig(
        run_id="golden-run-e2e",
        seed=20220101,
        data_snapshot_id="data-golden-v2",
        feature_version_id="feature-golden-v2",
        model_version_id="model-golden-v2",
        logic_version_id="TRACE-001-v1",
        starting_capital_yen=10_000,
    )


def test_golden_race_persists_traces_then_reveals_result_and_evaluation(
    migrated_session: Session,
) -> None:
    case = load_golden_race_fixture(FIXTURE_PATH).cases[0]
    pipeline_config = config()
    pipeline_result = GoldenRacePipeline(pipeline_config).run(case)
    assert pipeline_result.status == "succeeded"

    persistence = GoldenRacePersistenceRepository(migrated_session)
    recommendation_id = persistence.persist_pipeline_result(
        pipeline_result,
        case=case,
        config=pipeline_config,
    )

    assert migrated_session.query(CalculationArtifact).count() == 11
    assert migrated_session.query(LogicTrace).count() == 11
    with pytest.raises(ResultNotAvailableError):
        ResultRepository(migrated_session).reveal(
            race_id=case.race_id,
            recommendation_id=recommendation_id,
        )

    ResultRepository(migrated_session).add(
        Result(
            result_id=f"result:{case.race_id}",
            race_id=case.race_id,
            recommendation_id=recommendation_id,
            payload=case.outcome | {"payouts": case.payouts},
            persisted_at=NOW,
        ),
    )
    persistence.add_evaluation(
        Evaluation(
            evaluation_id=f"evaluation:{case.race_id}",
            race_id=case.race_id,
            recommendation_id=recommendation_id,
            prediction_metrics={"top1_correct": True},
            betting_metrics={"payout_yen": 280},
            odds_coverage_status="complete",
            logic_version_id=pipeline_config.logic_version_id,
            created_at=NOW,
        ),
    )

    revealed = ResultRepository(migrated_session).reveal(
        race_id=case.race_id,
        recommendation_id=recommendation_id,
    )
    assert revealed.payload["winner"] == "horse-1"
    assert migrated_session.get(Evaluation, f"evaluation:{case.race_id}") is not None

