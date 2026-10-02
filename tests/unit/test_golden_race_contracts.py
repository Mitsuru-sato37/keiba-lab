from dataclasses import FrozenInstanceError
from datetime import UTC
from pathlib import Path

import pytest
from keiba_application.golden_race import (
    GOLDEN_STAGE_ORDER,
    GoldenRaceFixture,
    Lineage,
    RecommendationDecision,
    StageArtifact,
    StageId,
    load_golden_race_fixture,
)

FIXTURE_PATH = Path("fixtures/golden-race/fixture.json")


def test_stage_artifact_is_immutable_and_carries_lineage() -> None:
    lineage = Lineage(
        data_snapshot_id="data-1",
        feature_version_id="feature-v1",
        model_version_id="model-v1",
        logic_version_id="TRACE-001-v1",
        input_ids=("feature-1",),
    )
    artifact = StageArtifact.create(
        artifact_id="artifact-1",
        run_id="run-1",
        race_id="race-1",
        stage=StageId.PREDICTION,
        output={"winner": "horse-1"},
        lineage=lineage,
    )

    assert artifact.stage is StageId.PREDICTION
    assert artifact.lineage == lineage
    assert artifact.status == "succeeded"
    with pytest.raises(FrozenInstanceError):
        artifact.status = "invalid"  # type: ignore[misc]


def test_stage_order_matches_the_gated_golden_race_flow() -> None:
    assert GOLDEN_STAGE_ORDER == (
        StageId.DATA_SNAPSHOT,
        StageId.FEATURE_SNAPSHOT,
        StageId.PREDICTION,
        StageId.CALIBRATION,
        StageId.SIMULATION,
        StageId.BET_PROBABILITY,
        StageId.ODDS_SNAPSHOT,
        StageId.EV,
        StageId.STRATEGY,
        StageId.MONEY_ALLOCATION,
        StageId.RECOMMENDATION,
        StageId.RESULT,
        StageId.EVALUATION,
    )


def test_fixture_has_reproducible_buy_and_skip_cases() -> None:
    fixture = load_golden_race_fixture(FIXTURE_PATH)

    assert isinstance(fixture, GoldenRaceFixture)
    assert fixture.fixture_version == "golden-race-v2"
    assert fixture.seed == 20220101
    assert {case.expected_decision for case in fixture.cases} == {
        RecommendationDecision.BUY,
        RecommendationDecision.SKIP,
    }
    assert all(case.prediction_inputs.get("odds") is None for case in fixture.cases)


def test_fixture_timestamps_are_temporally_ordered_and_utc() -> None:
    fixture = load_golden_race_fixture(FIXTURE_PATH)

    for case in fixture.cases:
        assert case.as_of_time.value.tzinfo is UTC
        assert case.odds_received_at.value.tzinfo is UTC
        assert case.odds_snapshot_time.value.tzinfo is UTC
        assert case.odds_received_at.value <= case.odds_snapshot_time.value
        assert all(
            feature.effective_at.value <= case.as_of_time.value
            for feature in case.runner_features
        )

