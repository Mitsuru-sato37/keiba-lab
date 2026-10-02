from datetime import UTC
from pathlib import Path

from keiba_infrastructure.validation_fixture import (
    OneDayValidationInputProvider,
    load_one_day_validation_fixture,
)

ROOT = Path(__file__).parents[2]
FIXTURE_PATH = ROOT / "fixtures" / "validation" / "2022-one-day" / "fixture.json"


def test_one_day_fixture_exposes_stable_2022_validation_contract() -> None:
    fixture = load_one_day_validation_fixture(FIXTURE_PATH)

    assert fixture.fixture_version == "2022-one-day-v1"
    assert fixture.seed == 20220105
    assert fixture.target_date.isoformat() == "2022-01-05"
    assert tuple(example.race_year for example in fixture.training_examples) == (
        2019,
        2020,
        2021,
    )
    assert tuple(race.race_id for race in fixture.races) == (
        "validation-2022-0105-r01",
        "validation-2022-0105-r02",
    )
    assert {item.decision for item in fixture.expected_recommendations.values()} == {
        "BUY",
        "SKIP",
    }
    assert fixture.races[0].feature_vectors[0].values == {"runner.gate": 1}
    assert fixture.races[0].observations[0].payload.get("odds") is None
    assert fixture.checksum == load_one_day_validation_fixture(FIXTURE_PATH).checksum


def test_one_day_fixture_is_temporally_eligible_and_uses_utc() -> None:
    fixture = load_one_day_validation_fixture(FIXTURE_PATH)

    for race in fixture.races:
        assert race.as_of_time.value.tzinfo is UTC
        for observation in race.observations:
            assert observation.received_timestamp.value <= race.as_of_time.value
            assert observation.effective_from.value <= race.as_of_time.value
        for vector in race.feature_vectors:
            assert vector.as_of_time.value <= race.as_of_time.value
            assert all("odds" not in key.lower() for key in vector.values)


def test_one_day_provider_filters_training_and_orders_2022_races() -> None:
    fixture = load_one_day_validation_fixture(FIXTURE_PATH)
    provider = OneDayValidationInputProvider(fixture)

    examples = provider.training_examples((2019, 2021))
    races = provider.races(2022)

    assert tuple(example.race_year for example in examples) == (2019, 2021)
    assert tuple(race.race_id for race in races) == (
        "validation-2022-0105-r01",
        "validation-2022-0105-r02",
    )
    assert races == fixture.races


def test_one_day_provider_rejects_unsupported_test_year() -> None:
    fixture = load_one_day_validation_fixture(FIXTURE_PATH)
    provider = OneDayValidationInputProvider(fixture)

    try:
        provider.races(2023)
    except ValueError as error:
        assert str(error) == "the one-day validation fixture supports test year 2022 only"
    else:
        raise AssertionError("unsupported test year should be rejected")
