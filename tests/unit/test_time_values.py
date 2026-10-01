from datetime import UTC, datetime

import pytest
from keiba_domain.identifiers import AppVersion
from keiba_domain.time_values import UtcInstant


def test_utc_instant_normalizes_aware_datetime_to_utc() -> None:
    instant = UtcInstant.from_datetime(
        datetime(2022, 1, 2, 3, 0, tzinfo=UTC),
    )

    assert instant.value.tzinfo is UTC
    assert instant.value.isoformat() == "2022-01-02T03:00:00+00:00"
    assert instant.to_tokyo().isoformat() == "2022-01-02T12:00:00+09:00"


def test_utc_instant_rejects_naive_datetime() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        UtcInstant.from_datetime(datetime(2022, 1, 2, 3, 0))


def test_app_version_rejects_blank_values() -> None:
    with pytest.raises(ValueError, match="non-empty"):
        AppVersion(" ")
