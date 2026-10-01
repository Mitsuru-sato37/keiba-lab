from datetime import UTC, datetime

import pytest
from keiba_application.errors import PredictionInvariantError, TrainingLeakError
from keiba_application.predictions import (
    PredictionSnapshot,
    RunnerPrediction,
    TrainingExample,
    TrainingManifest,
)
from keiba_domain.time_values import UtcInstant


def instant() -> UtcInstant:
    return UtcInstant.from_datetime(datetime(2022, 1, 1, 10, tzinfo=UTC))


def example(
    example_id: str,
    race_year: int,
    *,
    feature_version_id: str = "core-feature-v1",
    gate: int = 1,
) -> TrainingExample:
    return TrainingExample(
        example_id=example_id,
        race_id=f"race-{example_id}",
        runner_id=f"runner-{example_id}",
        race_year=race_year,
        feature_version_id=feature_version_id,
        features={"runner.gate": gate},
        won=race_year == 2021,
        top2=True,
        top3=True,
    )


def make_manifest(examples: tuple[TrainingExample, ...]) -> TrainingManifest:
    return TrainingManifest.create(
        manifest_id="training-2022-v1",
        test_year=2022,
        training_years=(2019, 2020, 2021),
        examples=examples,
        feature_version_id="core-feature-v1",
        model_version_id="baseline-gate-v1",
        logic_version_id="MODEL-BASE-001-v1",
    )


def test_manifest_accepts_exact_2022_walk_forward_window() -> None:
    manifest = make_manifest(
        (
            example("e-2021", 2021),
            example("e-2019", 2019),
            example("e-2020", 2020),
        ),
    )

    assert manifest.test_year == 2022
    assert manifest.training_years == (2019, 2020, 2021)
    assert manifest.training_example_ids == ("e-2019", "e-2020", "e-2021")
    assert len(manifest.checksum) == 64


@pytest.mark.parametrize(
    ("training_years", "examples"),
    [
        ((2019, 2021), (example("e-2019", 2019), example("e-2021", 2021))),
        (
            (2019, 2020, 2021),
            (example("e-2019", 2019), example("e-2020", 2020), example("e-2022", 2022)),
        ),
        ((2019, 2020, 2021), ()),
    ],
)
def test_manifest_rejects_missing_training_year(
    training_years: tuple[int, ...],
    examples: tuple[TrainingExample, ...],
) -> None:
    with pytest.raises(TrainingLeakError):
        TrainingManifest.create(
            manifest_id="invalid-training",
            test_year=2022,
            training_years=training_years,
            examples=examples,
            feature_version_id="core-feature-v1",
            model_version_id="baseline-gate-v1",
            logic_version_id="MODEL-BASE-001-v1",
        )


def test_manifest_rejects_feature_version_mismatch() -> None:
    examples = (example("e-2019", 2019, feature_version_id="other-feature"),)

    with pytest.raises(TrainingLeakError, match="feature version"):
        make_manifest(examples + (example("e-2020", 2020), example("e-2021", 2021)))


def test_manifest_checksum_is_independent_of_example_order() -> None:
    first = make_manifest(
        (example("e-2019", 2019), example("e-2020", 2020), example("e-2021", 2021)),
    )
    second = make_manifest(
        (example("e-2021", 2021), example("e-2019", 2019), example("e-2020", 2020)),
    )

    assert first.checksum == second.checksum


def runner_prediction(runner_id: str, win: float) -> RunnerPrediction:
    return RunnerPrediction(
        runner_id=runner_id,
        raw_win_probability=win,
        win_probability=win,
        raw_top2_probability=min(1.0, win + 0.2),
        top2_probability=min(1.0, win + 0.2),
        raw_top3_probability=min(1.0, win + 0.4),
        top3_probability=min(1.0, win + 0.4),
        ranking_score=win,
        uncertainty=0.5,
        disagreement=0.0,
    )


def snapshot(*predictions: RunnerPrediction) -> PredictionSnapshot:
    return PredictionSnapshot(
        prediction_snapshot_id="prediction-1",
        race_id="race-1",
        as_of_time=instant(),
        data_snapshot_id="snapshot-1",
        feature_version_id="core-feature-v1",
        model_version_id="baseline-gate-v1",
        logic_version_id="MODEL-BASE-001-v1",
        training_manifest_id="training-2022-v1",
        model_manifest_checksum="a" * 64,
        calibration_version_id=None,
        predictions=predictions,
    )


def test_prediction_snapshot_accepts_coherent_probabilities() -> None:
    result = snapshot(runner_prediction("runner-1", 0.25), runner_prediction("runner-2", 0.75))

    assert result.prediction_snapshot_id == "prediction-1"


def test_prediction_snapshot_rejects_non_normalized_win_probabilities() -> None:
    with pytest.raises(PredictionInvariantError, match="sum"):
        snapshot(runner_prediction("runner-1", 0.25), runner_prediction("runner-2", 0.25))


def test_runner_prediction_rejects_probability_ordering() -> None:
    with pytest.raises(PredictionInvariantError, match="top"):
        RunnerPrediction(
            runner_id="runner-1",
            raw_win_probability=0.7,
            win_probability=0.7,
            raw_top2_probability=0.6,
            top2_probability=0.6,
            raw_top3_probability=0.8,
            top3_probability=0.8,
            ranking_score=0.7,
            uncertainty=0.5,
            disagreement=0.0,
        )
