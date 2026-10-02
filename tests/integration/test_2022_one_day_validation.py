from dataclasses import replace
from datetime import timedelta
from pathlib import Path

from keiba_application.backtest import BacktestStatus
from keiba_domain.time_values import UtcInstant
from keiba_infrastructure.validation_fixture import load_one_day_validation_fixture
from keiba_infrastructure.validation_runner import (
    OneDayValidationReport,
    run_one_day_validation,
)

ROOT = Path(__file__).parents[2]
FIXTURE_PATH = ROOT / "fixtures" / "validation" / "2022-one-day" / "fixture.json"


def test_one_day_validation_runs_walk_forward_order_and_both_decisions() -> None:
    fixture = load_one_day_validation_fixture(FIXTURE_PATH)

    report = run_one_day_validation(fixture)

    assert isinstance(report, OneDayValidationReport)
    assert report.result.status is BacktestStatus.SUCCEEDED
    assert report.result.fold_ids == ("fold-2022",)
    assert report.ordered_race_ids == (
        "validation-2022-0105-r01",
        "validation-2022-0105-r02",
    )
    assert report.recommendation_decisions == {
        "validation-2022-0105-r01": "BUY",
        "validation-2022-0105-r02": "SKIP",
    }
    assert report.result.prediction_metrics == {"result_count": 2}
    assert report.result.betting_metrics is None
    assert report.events.index(
        "persist-recommendation:validation-2022-0105-r01",
    ) < report.events.index("result:validation-2022-0105-r01")


def test_one_day_validation_replay_is_deterministic() -> None:
    fixture = load_one_day_validation_fixture(FIXTURE_PATH)

    first = run_one_day_validation(fixture)
    second = run_one_day_validation(fixture)

    assert first == second
    assert first.fixture_checksum == fixture.checksum


def test_future_observation_invalidates_one_day_run_before_prediction() -> None:
    fixture = load_one_day_validation_fixture(FIXTURE_PATH)
    race = fixture.races[0]
    future = UtcInstant.from_datetime(race.as_of_time.value + timedelta(minutes=1))
    invalid_observation = replace(race.observations[0], received_timestamp=future)
    invalid_race = replace(
        race,
        observations=(invalid_observation, *race.observations[1:]),
    )
    invalid_fixture = replace(fixture, races=(invalid_race, fixture.races[1]))

    report = run_one_day_validation(invalid_fixture)

    assert report.result.status is BacktestStatus.INVALID
    assert not any(event.startswith("predict:") for event in report.events)
    assert not any(event.startswith("result:") for event in report.events)


def test_current_race_odds_invalidates_one_day_run_before_prediction() -> None:
    fixture = load_one_day_validation_fixture(FIXTURE_PATH)
    race = fixture.races[0]
    vector = replace(
        race.feature_vectors[0],
        values={"runner.gate": 1, "current_odds": 2.5},
    )
    invalid_race = replace(
        race,
        feature_vectors=(vector, *race.feature_vectors[1:]),
    )
    invalid_fixture = replace(fixture, races=(invalid_race, fixture.races[1]))

    report = run_one_day_validation(invalid_fixture)

    assert report.result.status is BacktestStatus.INVALID
    assert not any(event.startswith("predict:") for event in report.events)
    assert not any(event.startswith("result:") for event in report.events)
