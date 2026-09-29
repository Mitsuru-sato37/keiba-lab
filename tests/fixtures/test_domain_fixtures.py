from datetime import timedelta

from tests.fixtures.domain import fixture_metadata


def test_fixture_metadata_is_deterministic_and_utc() -> None:
    first = fixture_metadata()
    second = fixture_metadata()
    assert first == second
    assert first["as_of_time"].utcoffset() == timedelta(0)  # type: ignore[union-attr]
    assert isinstance(first["simulation_seed"], int)
    assert first["simulation_seed"] > 0
