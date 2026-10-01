from dataclasses import replace
from datetime import UTC, datetime
from math import isclose
from typing import Any

import pytest
from keiba_application.errors import OddsLeakError, PredictionInvariantError, TrainingLeakError
from keiba_application.predictions import TrainingExample, TrainingManifest
from keiba_application.snapshots import FeatureVector
from keiba_domain.time_values import UtcInstant
from keiba_infrastructure.baseline_prediction import (
    GateStrengthBaseline,
    TrainedGateStrengthBaseline,
)


def instant() -> UtcInstant:
    return UtcInstant.from_datetime(datetime(2022, 1, 1, 10, tzinfo=UTC))


def training_example(
    example_id: str,
    race_year: int,
    gate: int,
    won: bool,
) -> TrainingExample:
    return TrainingExample(
        example_id=example_id,
        race_id=f"race-{example_id}",
        runner_id=f"runner-{example_id}",
        race_year=race_year,
        feature_version_id="core-feature-v1",
        features={"runner.gate": gate},
        won=won,
        top2=won,
        top3=won,
    )


def training_examples() -> tuple[TrainingExample, ...]:
    return (
        training_example("e-2019-a", 2019, 1, True),
        training_example("e-2019-b", 2019, 1, False),
        training_example("e-2020-a", 2020, 2, False),
        training_example("e-2020-b", 2020, 2, False),
        training_example("e-2021-a", 2021, 1, True),
        training_example("e-2021-b", 2021, 2, True),
    )


def manifest(examples: tuple[TrainingExample, ...]) -> TrainingManifest:
    return TrainingManifest.create(
        manifest_id="training-2022-v1",
        test_year=2022,
        training_years=(2019, 2020, 2021),
        examples=examples,
        feature_version_id="core-feature-v1",
        model_version_id="baseline-gate-v1",
        logic_version_id="MODEL-BASE-001-v1",
    )


def feature_vector(
    runner_id: str,
    gate: int | None,
    *,
    race_id: str = "race-test",
    snapshot_id: str = "snapshot-test",
    as_of: UtcInstant | None = None,
    feature_version_id: str = "core-feature-v1",
    extra_values: dict[str, object] | None = None,
) -> FeatureVector:
    values: dict[str, object] = {}
    if gate is not None:
        values["runner.gate"] = gate
    if extra_values:
        values.update(extra_values)
    return FeatureVector(
        feature_snapshot_id=f"feature-{runner_id}",
        race_id=race_id,
        runner_id=runner_id,
        as_of_time=as_of or instant(),
        data_snapshot_id=snapshot_id,
        feature_version_id=feature_version_id,
        logic_version_id="FEAT-001-v1",
        values=values,
        source_observation_ids=("race-observation", f"observation-{runner_id}"),
        missing_fields=(),
    )


def fitted_model() -> tuple[TrainedGateStrengthBaseline, tuple[TrainingExample, ...]]:
    examples = training_examples()
    return GateStrengthBaseline.fit(manifest=manifest(examples), examples=examples), examples


def test_baseline_fit_rejects_example_outside_manifest() -> None:
    model_examples = training_examples()
    extra = training_example("e-extra", 2021, 3, False)

    with pytest.raises(TrainingLeakError, match="manifest"):
        GateStrengthBaseline.fit(
            manifest=manifest(model_examples),
            examples=model_examples + (extra,),
        )


def test_prediction_preserves_manifest_model_version() -> None:
    examples = training_examples()
    manifest_v2 = TrainingManifest.create(
        manifest_id="training-2022-v2",
        test_year=2022,
        training_years=(2019, 2020, 2021),
        examples=examples,
        feature_version_id="core-feature-v1",
        model_version_id="baseline-gate-v2",
        logic_version_id="MODEL-BASE-001-v1",
    )
    model = GateStrengthBaseline.fit(manifest=manifest_v2, examples=examples)

    result = model.predict((feature_vector("runner-1", 1),))

    assert result.model_version_id == "baseline-gate-v2"
    assert result.logic_version_id == "MODEL-BASE-001-v1"


def test_gate_strength_uses_binary_laplace_rates_and_overall_prior() -> None:
    model, _ = fitted_model()

    result = model.predict(
        (
            feature_vector("runner-gate-1", 1),
            feature_vector("runner-gate-2", 2),
        ),
    )

    gate_one, gate_two = result.predictions
    assert isclose(gate_one.ranking_score, 3 / 5)
    assert isclose(gate_two.ranking_score, 2 / 5)
    assert isclose(gate_one.win_probability, 0.6)
    assert isclose(gate_two.win_probability, 0.4)


def test_baseline_prediction_is_deterministic() -> None:
    model, _ = fitted_model()
    vectors = (feature_vector("runner-2", 2), feature_vector("runner-1", 1))

    first = model.predict(vectors)
    second = model.predict(vectors)

    assert first == second
    assert first.predictions[0].runner_id == "runner-1"


def test_prediction_probabilities_are_coherent() -> None:
    model, _ = fitted_model()
    result = model.predict(
        (
            feature_vector("runner-1", 1),
            feature_vector("runner-2", 2),
            feature_vector("runner-3", 9),
        ),
    )

    assert isclose(sum(prediction.win_probability for prediction in result.predictions), 1.0)
    for prediction in result.predictions:
        assert 0.0 <= prediction.win_probability <= 1.0
        assert 0.0 <= prediction.top2_probability <= 1.0
        assert 0.0 <= prediction.top3_probability <= 1.0
        assert prediction.win_probability <= prediction.top2_probability
        assert prediction.top2_probability <= prediction.top3_probability


def test_one_runner_prediction_is_coherent() -> None:
    model, _ = fitted_model()

    result = model.predict((feature_vector("runner-only", 1),))

    assert result.predictions[0].win_probability == 1.0
    assert result.predictions[0].top2_probability == 1.0
    assert result.predictions[0].top3_probability == 1.0


def test_unseen_gate_uses_training_prior() -> None:
    model, _ = fitted_model()

    result = model.predict((feature_vector("runner-unseen", 9),))

    prediction = result.predictions[0]
    assert isclose(prediction.ranking_score, 0.5)
    assert prediction.uncertainty == 1.0


def test_missing_gate_uses_training_prior() -> None:
    model, _ = fitted_model()

    result = model.predict((feature_vector("runner-missing", None),))

    assert isclose(result.predictions[0].ranking_score, 0.5)
    assert result.predictions[0].uncertainty == 1.0


def test_prediction_rejects_current_race_odds() -> None:
    model, _ = fitted_model()

    with pytest.raises(OddsLeakError, match="odds"):
        model.predict(
            (
                feature_vector(
                    "runner-odds",
                    1,
                    extra_values={"current_odds": 2.5},
                ),
            ),
        )


@pytest.mark.parametrize(
    "changed",
    [
        {"race_id": "other-race"},
        {"data_snapshot_id": "other-snapshot"},
        {"as_of_time": UtcInstant.from_datetime(datetime(2022, 1, 1, 11, tzinfo=UTC))},
        {"feature_version_id": "other-feature"},
    ],
)
def test_prediction_rejects_mixed_feature_context(changed: dict[str, Any]) -> None:
    model, _ = fitted_model()
    first = feature_vector("runner-1", 1)
    second = replace(feature_vector("runner-2", 2), **changed)

    with pytest.raises(PredictionInvariantError, match="context"):
        model.predict((first, second))
