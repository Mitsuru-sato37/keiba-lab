from datetime import UTC, datetime
from decimal import Decimal

from keiba_lab.providers.ports import OddsRecord, RaceRecord, RunnerRecord, require_utc


class FixtureProvider:
    def __init__(self) -> None:
        received = datetime(2022, 1, 1, tzinfo=UTC)
        runner = RunnerRecord(
            provider="FIXTURE",
            provider_key="R202201010101:H1",
            received_timestamp=received,
            effective_from=received,
            snapshot_id="SNAP-R1",
            payload_checksum="fixture-r1-h1",
            horse_id="H1",
            horse_number=1,
        )
        self._race = RaceRecord(
            provider="FIXTURE",
            provider_key="R202201010101",
            received_timestamp=received,
            effective_from=received,
            snapshot_id="SNAP-R1",
            payload_checksum="fixture-r1",
            race_id="R202201010101",
            scheduled_post_time=datetime(2022, 1, 1, 6, tzinfo=UTC),
            runners=(runner,),
        )
        self._odds = (
            OddsRecord(
                provider="FIXTURE",
                provider_key="R202201010101:H1:1",
                received_timestamp=received,
                effective_from=datetime(2022, 1, 1, 1, tzinfo=UTC),
                snapshot_id="ODDS-1",
                payload_checksum="fixture-odds-1",
                race_id="R202201010101",
                horse_id="H1",
                current_odds=Decimal("4.0"),
            ),
            OddsRecord(
                provider="FIXTURE",
                provider_key="R202201010101:H1:2",
                received_timestamp=received,
                effective_from=datetime(2022, 1, 1, 2, tzinfo=UTC),
                snapshot_id="ODDS-2",
                payload_checksum="fixture-odds-2",
                race_id="R202201010101",
                horse_id="H1",
                current_odds=Decimal("5.0"),
            ),
        )

    def list_races(self, as_of_time: datetime) -> tuple[RaceRecord, ...]:
        as_of = require_utc(as_of_time)
        return (
            (self._race,)
            if self._race.received_timestamp <= as_of and self._race.effective_from <= as_of
            else ()
        )

    def get_race(self, race_id: str, as_of_time: datetime) -> RaceRecord | None:
        return self._race if race_id == self._race.race_id and self.list_races(as_of_time) else None

    def get_odds(self, race_id: str, as_of_time: datetime) -> tuple[OddsRecord, ...]:
        as_of = require_utc(as_of_time)
        eligible = [
            row
            for row in self._odds
            if row.race_id == race_id
            and row.received_timestamp <= as_of
            and row.effective_from <= as_of
        ]
        return tuple(eligible[-1:])
