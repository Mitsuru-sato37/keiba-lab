from datetime import UTC, datetime

from keiba_lab.providers.fixture import FixtureProvider
from tests.fixtures.phase1 import FIXTURE_AS_OF


def test_fixture_provider_lists_deterministic_races_and_filters_as_of() -> None:
    provider = FixtureProvider()
    first = provider.list_races(FIXTURE_AS_OF)
    second = provider.list_races(FIXTURE_AS_OF)
    assert first == second
    assert first[0].race_id == "R202201010101"
    assert provider.list_races(datetime(2021, 12, 31, 23, 59, tzinfo=UTC)) == ()


def test_fixture_provider_odds_respect_effective_time_and_promotion() -> None:
    provider = FixtureProvider()
    assert (
        provider.get_odds("R202201010101", datetime(2022, 1, 1, 1, 30, tzinfo=UTC))[0].current_odds
        == 4.0
    )
    assert (
        provider.get_odds("R202201010101", datetime(2022, 1, 1, 2, 30, tzinfo=UTC))[0].current_odds
        == 5.0
    )


def test_fixture_provider_exposes_provider_metadata() -> None:
    race = FixtureProvider().list_races(FIXTURE_AS_OF)[0]
    assert race.provider == "FIXTURE"
    assert race.snapshot_id.startswith("SNAP-")
