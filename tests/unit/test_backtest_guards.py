from datetime import UTC, datetime, timedelta

import pytest
from keiba_application.backtest import (
    GuardResult,
    GuardStatus,
    WalkForwardFold,
)
from keiba_application.backtest_guards import (
    BacktestGuards,
    RecommendationPersistenceGate,
    ResultAccessCapability,
)
from keiba_application.errors import GuardViolationError, ResultAccessDeniedError
from keiba_application.ports import ObservationRecord
from keiba_application.predictions import TrainingExample, TrainingManifest
from keiba_domain.time_values import UtcInstant

NOW = UtcInstant.from_datetime(datetime(2022, 1, 1, tzinfo=UTC))


def observation(
    record_id: str,
    *,
    received: UtcInstant = NOW,
    effective: UtcInstant = NOW,
    effective_to: UtcInstant | None = None,
    payload: dict[str, object] | None = None,
    record_type: str = "runner",
) -> ObservationRecord:
    return ObservationRecord(
        record_id=record_id,
        source="fixture",
        source_version="fixture-v1",
        source_timestamp=NOW,
        received_timestamp=received,
        effective_from=effective,
        effective_to=effective_to,
        payload=payload or {"race_id": "race-1", "runner_id": record_id},
        provider_record_type=record_type,
    )


def valid_training_manifest() -> TrainingManifest:
    examples = tuple(
        TrainingExample(
            example_id=f"example-{year}",
            race_id=f"race-{year}",
            runner_id=f"runner-{year}",
            race_year=year,
            feature_version_id="core-feature-v1",
            features={},
            won=False,
            top2=False,
            top3=False,
        )
        for year in (2019, 2020, 2021)
    )
    return TrainingManifest.create(
        manifest_id="training-2022-v1",
        test_year=2022,
        training_years=(2019, 2020, 2021),
        examples=examples,
        feature_version_id="core-feature-v1",
        model_version_id="baseline-gate-v1",
        logic_version_id="MODEL-BASE-001-v1",
    )


def test_temporal_guard_accepts_values_at_as_of_boundary() -> None:
    result = BacktestGuards.check_temporal_eligibility((observation("runner-1"),), NOW)

    assert result.guard_id == "LEAK-001"
    assert result.status is GuardStatus.PASS


@pytest.mark.parametrize(
    "record",
    [
        observation(
            "received-future",
            received=UtcInstant.from_datetime(NOW.value + timedelta(seconds=1)),
        ),
        observation(
            "effective-future",
            effective=UtcInstant.from_datetime(NOW.value + timedelta(seconds=1)),
        ),
        observation(
            "superseded",
            effective_to=UtcInstant.from_datetime(NOW.value),
        ),
    ],
)
def test_temporal_guard_rejects_future_or_superseded_inputs(record: ObservationRecord) -> None:
    result = BacktestGuards.check_temporal_eligibility((record,), NOW)

    assert result.guard_id == "LEAK-001"
    assert result.status is GuardStatus.FAIL
    assert result.checked_input_ids == (record.record_id,)


def test_training_guard_rejects_test_year_contamination() -> None:
    manifest = valid_training_manifest()
    contaminated = TrainingManifest(
        manifest_id=manifest.manifest_id,
        test_year=2022,
        training_years=(2019, 2020, 2021, 2022),
        training_example_ids=manifest.training_example_ids,
        feature_version_id=manifest.feature_version_id,
        model_version_id=manifest.model_version_id,
        logic_version_id=manifest.logic_version_id,
        checksum=manifest.checksum,
    )

    result = BacktestGuards.check_training_window(
        contaminated,
        WalkForwardFold.create(test_year=2022),
    )

    assert result.guard_id == "LEAK-002"
    assert result.status is GuardStatus.FAIL


@pytest.mark.parametrize(
    "inputs",
    [
        (observation("odds-record", record_type="odds"),),
        ({"features": {"market": {"closing_odds": 2.5}}},),
    ],
)
def test_ability_guard_rejects_direct_and_nested_odds(inputs: tuple[object, ...]) -> None:
    result = BacktestGuards.check_ability_inputs(inputs)

    assert result.guard_id == "LEAK-003"
    assert result.status is GuardStatus.FAIL


def test_version_guard_rejects_missing_and_mismatched_versions() -> None:
    result = BacktestGuards.check_versions(
        required_versions={"feature": "core-feature-v1", "model": "baseline-gate-v1"},
        artifact_versions={"feature": "core-feature-v1"},
    )

    assert result.guard_id == "VERSION-001"
    assert result.status is GuardStatus.FAIL


def test_require_pass_raises_for_any_failed_guard() -> None:
    failed = GuardResult.failed(
        guard_result_id="guard-1",
        guard_id="LEAK-002",
        guard_version="LEAK-002-v1",
        details={"reason": "test year"},
    )

    with pytest.raises(GuardViolationError, match="LEAK-002"):
        BacktestGuards.require_pass((failed,))


def test_result_capability_requires_every_recommendation_for_the_race() -> None:
    with pytest.raises(ResultAccessDeniedError):
        RecommendationPersistenceGate.issue(
            race_id="race-1",
            recommendation_ids=("recommendation-1", "recommendation-2"),
            persisted_ids=("recommendation-1",),
        )

    capability = RecommendationPersistenceGate.issue(
        race_id="race-1",
        recommendation_ids=("recommendation-1", "recommendation-2"),
        persisted_ids=("recommendation-1", "recommendation-2"),
    )

    assert capability.allows("race-1")
    assert not capability.allows("race-2")


def test_forged_result_capability_does_not_allow_result_access() -> None:
    forged = ResultAccessCapability(_race_id="race-1", _token="guess")

    assert not forged.allows("race-1")
