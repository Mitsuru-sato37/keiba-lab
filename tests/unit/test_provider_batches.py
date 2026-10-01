from keiba_infrastructure.fixtures import DeterministicFixtureProvider


def test_fixture_provider_returns_a_stable_batch() -> None:
    first = DeterministicFixtureProvider(seed=7, fixture_version="v1").collect()
    second = DeterministicFixtureProvider(seed=7, fixture_version="v1").collect()

    assert first == second
    assert first.provider == "deterministic-fixture"
    assert first.provider_version == "v1"
    assert first.records[0].provider_record_type == "observation"
    assert first.records[0].provider_record_key == first.records[0].record_id


def test_fixture_batch_changes_when_seed_changes() -> None:
    first = DeterministicFixtureProvider(seed=7, fixture_version="v1").collect()
    second = DeterministicFixtureProvider(seed=8, fixture_version="v1").collect()

    assert first != second
