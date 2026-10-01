from collections.abc import Mapping
from dataclasses import dataclass

from keiba_domain.time_values import UtcInstant


@dataclass(frozen=True, slots=True)
class RaceSnapshot:
    snapshot_id: str
    race_id: str
    as_of_time: UtcInstant
    race_observation_id: str
    race_payload: Mapping[str, object]
    runner_records: tuple[tuple[str, str, Mapping[str, object]], ...]
    observation_ids: tuple[str, ...]
    content_checksum: str

    @property
    def runner_ids(self) -> tuple[str, ...]:
        return tuple(record[0] for record in self.runner_records)


@dataclass(frozen=True, slots=True)
class FeatureVector:
    feature_snapshot_id: str
    race_id: str
    runner_id: str
    as_of_time: UtcInstant
    data_snapshot_id: str
    feature_version_id: str
    logic_version_id: str
    values: Mapping[str, object]
    source_observation_ids: tuple[str, ...]
    missing_fields: tuple[str, ...]
