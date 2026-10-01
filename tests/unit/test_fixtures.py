from keiba_infrastructure.fixtures import DeterministicFixtureProvider


def test_fixture_provider_is_stable_for_seed_and_version() -> None:
    first = DeterministicFixtureProvider(seed=7, fixture_version="v1").observations()
    second = DeterministicFixtureProvider(seed=7, fixture_version="v1").observations()

    assert first == second
    assert first[0].source == "deterministic-fixture"
    assert first[0].source_version == "v1"


def test_fixture_provider_changes_when_seed_changes() -> None:
    first = DeterministicFixtureProvider(seed=7, fixture_version="v1").observations()
    second = DeterministicFixtureProvider(seed=8, fixture_version="v1").observations()

    assert first != second
