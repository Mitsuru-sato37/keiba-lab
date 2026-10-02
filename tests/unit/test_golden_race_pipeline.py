from dataclasses import dataclass
from pathlib import Path

from keiba_application.golden_race import (
    GOLDEN_STAGE_ORDER,
    GoldenRacePipeline,
    PipelineConfig,
    PredictionInput,
    RecommendationDecision,
    load_golden_race_fixture,
)

FIXTURE_PATH = Path("fixtures/golden-race/fixture.json")


def make_config(*, seed: int = 20220101, logic_version_id: str = "SIM-001-v1") -> PipelineConfig:
    return PipelineConfig(
        run_id="golden-run-1",
        seed=seed,
        data_snapshot_id="data-golden-v1",
        feature_version_id="feature-golden-v1",
        model_version_id="model-golden-v1",
        logic_version_id=logic_version_id,
        starting_capital_yen=10_000,
    )


@dataclass
class SpyPredictor:
    inputs: list[PredictionInput]

    def predict(self, prediction_input: PredictionInput) -> dict[str, float]:
        self.inputs.append(prediction_input)
        scores = {}
        for feature in prediction_input.runner_features:
            form_score = feature.values["form_score"]
            assert isinstance(form_score, (int, float))
            scores[feature.runner_id] = float(form_score)
        total = sum(scores.values())
        return {runner_id: score / total for runner_id, score in scores.items()}


def test_pipeline_is_reproducible_and_ability_predictor_never_receives_odds() -> None:
    case = load_golden_race_fixture(FIXTURE_PATH).cases[0]
    first_spy = SpyPredictor([])
    second_spy = SpyPredictor([])

    first = GoldenRacePipeline(make_config()).run(case, predictor=first_spy)
    second = GoldenRacePipeline(make_config()).run(case, predictor=second_spy)

    assert first.status == "succeeded"
    assert second.status == "succeeded"
    assert first.decision is RecommendationDecision.BUY
    assert first.decision == second.decision
    assert first.selected_runner_id == second.selected_runner_id
    assert first.allocation_yen == second.allocation_yen
    assert [artifact.checksum for artifact in first.artifacts] == [
        artifact.checksum for artifact in second.artifacts
    ]
    assert len(first_spy.inputs) == 1
    assert first_spy.inputs[0].prediction_inputs == case.prediction_inputs
    assert not hasattr(first_spy.inputs[0], "odds")


def test_simulation_changes_when_seed_changes() -> None:
    case = load_golden_race_fixture(FIXTURE_PATH).cases[0]

    first = GoldenRacePipeline(make_config(seed=20220101)).run(case)
    second = GoldenRacePipeline(make_config(seed=20220102)).run(case)

    first_simulation = next(
        artifact for artifact in first.artifacts if artifact.stage.value == "simulation"
    )
    second_simulation = next(
        artifact for artifact in second.artifacts if artifact.stage.value == "simulation"
    )
    assert first_simulation.checksum != second_simulation.checksum


def test_pipeline_produces_buy_and_skip_with_explicit_reason() -> None:
    fixture = load_golden_race_fixture(FIXTURE_PATH)

    buy = GoldenRacePipeline(make_config()).run(fixture.cases[0])
    skip = GoldenRacePipeline(make_config()).run(fixture.cases[1])

    assert buy.decision is RecommendationDecision.BUY
    assert buy.decision_reason is None
    assert skip.decision is RecommendationDecision.SKIP
    assert skip.decision_reason == "SKIP_NO_VALUE"
    assert skip.allocation_yen == 0


def test_version_guard_invalidates_the_complete_run() -> None:
    case = load_golden_race_fixture(FIXTURE_PATH).cases[0]

    result = GoldenRacePipeline(make_config(logic_version_id="")).run(case)

    assert result.status == "invalid"
    assert result.decision is None
    assert result.artifacts == ()
    assert "version" in result.diagnostic.lower()


def test_pipeline_contract_exposes_the_full_gated_stage_order() -> None:
    assert GoldenRacePipeline.stage_order() == GOLDEN_STAGE_ORDER[:11]
