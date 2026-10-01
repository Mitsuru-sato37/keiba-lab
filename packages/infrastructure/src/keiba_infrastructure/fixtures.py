import random
from datetime import UTC, datetime

from keiba_application.ports import ObservationRecord
from keiba_domain.time_values import UtcInstant


class DeterministicFixtureProvider:
    def __init__(self, *, seed: int, fixture_version: str) -> None:
        self._seed = seed
        self._fixture_version = fixture_version

    def observations(self) -> tuple[ObservationRecord, ...]:
        random_source = random.Random(self._seed)
        received = UtcInstant.from_datetime(datetime(2022, 1, 1, tzinfo=UTC))
        records = tuple(
            ObservationRecord(
                record_id=f"fixture-race-{index}",
                source="deterministic-fixture",
                source_version=self._fixture_version,
                source_timestamp=received,
                received_timestamp=received,
                effective_from=received,
                payload={"value": random_source.randint(1, 100)},
            )
            for index in range(3)
        )
        return records
