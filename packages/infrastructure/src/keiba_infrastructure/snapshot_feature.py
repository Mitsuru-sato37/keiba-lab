import hashlib
import json
from collections.abc import Iterable, Mapping
from datetime import UTC, datetime

from keiba_application.errors import OddsLeakError, TemporalLeakError
from keiba_application.ports import ObservationRecord
from keiba_application.snapshots import FeatureVector, RaceSnapshot
from keiba_domain.time_values import UtcInstant
from sqlalchemy.orm import Session

from .schema import DataSnapshot, FeatureSnapshot

CORE_FEATURE_VERSION_ID = "core-feature-v1"
CORE_FEATURE_LOGIC_VERSION_ID = "FEAT-001-v1"


def _has_odds(payload: Mapping[str, object]) -> bool:
    return any("odds" in key.lower() for key in payload)


def _checksum(value: Mapping[str, object]) -> str:
    serialized = json.dumps(dict(value), sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


class RaceSnapshotBuilder:
    def build(
        self,
        *,
        race_id: str,
        as_of_time: UtcInstant,
        observations: Iterable[ObservationRecord],
        snapshot_id: str | None = None,
    ) -> RaceSnapshot:
        records = tuple(observations)
        if len({record.record_id for record in records}) != len(records):
            raise ValueError("snapshot observations must have unique record IDs")

        for record in records:
            if record.received_timestamp.value > as_of_time.value:
                raise TemporalLeakError(
                    f"{record.record_id} has received_timestamp after as_of_time",
                )
            if record.effective_from.value > as_of_time.value:
                raise TemporalLeakError(
                    f"{record.record_id} has effective_from after as_of_time",
                )
            if record.effective_to is not None and record.effective_to.value <= as_of_time.value:
                raise TemporalLeakError(f"{record.record_id} was superseded at as_of_time")
            if record.provider_record_type == "odds" or _has_odds(record.payload):
                raise OddsLeakError("current-race odds cannot enter an ability snapshot")
            payload_race_id = record.payload.get("race_id")
            if payload_race_id != race_id:
                raise ValueError(f"observation {record.record_id} belongs to another race")

        race_records = tuple(record for record in records if record.provider_record_type == "race")
        runner_records = tuple(
            record for record in records if record.provider_record_type == "runner"
        )
        if len(race_records) != 1:
            raise ValueError("snapshot requires exactly one race record")
        if not runner_records:
            raise ValueError("snapshot requires at least one runner record")

        race_record = race_records[0]
        runner_members: list[tuple[str, str, Mapping[str, object]]] = []
        for record in runner_records:
            runner_id = record.payload.get("runner_id")
            if not isinstance(runner_id, str) or not runner_id:
                raise ValueError(f"runner record {record.record_id} has no runner_id")
            runner_members.append((runner_id, record.record_id, dict(record.payload)))
        runner_members.sort(key=lambda member: member[0])

        membership = {
            "race_id": race_id,
            "as_of_time": as_of_time.value.isoformat(),
            "race_observation_id": race_record.record_id,
            "race_payload": dict(race_record.payload),
            "runner_records": runner_members,
        }
        content_checksum = _checksum(membership)
        resolved_snapshot_id = snapshot_id or f"snapshot-{race_id}-{content_checksum[:16]}"
        return RaceSnapshot(
            snapshot_id=resolved_snapshot_id,
            race_id=race_id,
            as_of_time=as_of_time,
            race_observation_id=race_record.record_id,
            race_payload=dict(race_record.payload),
            runner_records=tuple(runner_members),
            observation_ids=tuple(sorted(record.record_id for record in records)),
            content_checksum=content_checksum,
        )


class CoreFeatureV1Registry:
    feature_version_id = CORE_FEATURE_VERSION_ID
    logic_version_id = CORE_FEATURE_LOGIC_VERSION_ID

    def generate(self, snapshot: RaceSnapshot, *, runner_id: str) -> FeatureVector:
        runner_record = next(
            (record for record in snapshot.runner_records if record[0] == runner_id),
            None,
        )
        if runner_record is None:
            raise KeyError(f"runner {runner_id} is not in snapshot {snapshot.snapshot_id}")

        _, runner_observation_id, runner_payload = runner_record
        if _has_odds(snapshot.race_payload) or _has_odds(runner_payload):
            raise OddsLeakError("current-race odds cannot enter Core Feature v1")

        values: dict[str, object] = {}
        missing: list[str] = []

        def add_feature(name: str, payload: Mapping[str, object], key: str) -> None:
            if key not in payload:
                values[name] = None
                missing.append(name)
            else:
                values[name] = payload[key]

        add_feature("race.distance_m", snapshot.race_payload, "distance_m")
        add_feature("race.field_size", snapshot.race_payload, "field_size")
        if "surface" not in snapshot.race_payload:
            values["race.surface_turf"] = None
            missing.append("race.surface_turf")
        else:
            values["race.surface_turf"] = snapshot.race_payload["surface"] == "turf"
        add_feature("runner.gate", runner_payload, "gate")
        add_feature("runner.horse_number", runner_payload, "horse_number")
        add_feature("runner.age", runner_payload, "age")
        add_feature("runner.carried_weight_kg", runner_payload, "carried_weight_kg")
        add_feature("runner.days_since_last_race", runner_payload, "days_since_last_race")

        feature_id = hashlib.sha256(
            f"{snapshot.snapshot_id}:{runner_id}:{self.feature_version_id}".encode(),
        ).hexdigest()[:24]
        return FeatureVector(
            feature_snapshot_id=f"feature-{feature_id}",
            race_id=snapshot.race_id,
            runner_id=runner_id,
            as_of_time=snapshot.as_of_time,
            data_snapshot_id=snapshot.snapshot_id,
            feature_version_id=self.feature_version_id,
            logic_version_id=self.logic_version_id,
            values=values,
            source_observation_ids=(snapshot.race_observation_id, runner_observation_id),
            missing_fields=tuple(missing),
        )


class DataSnapshotRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, snapshot: RaceSnapshot) -> None:
        manifest = {
            "race_id": snapshot.race_id,
            "observation_ids": list(snapshot.observation_ids),
            "race_observation_id": snapshot.race_observation_id,
            "runner_ids": list(snapshot.runner_ids),
            "content_checksum": snapshot.content_checksum,
        }
        self._session.add(
            DataSnapshot(
                snapshot_id=snapshot.snapshot_id,
                as_of_time=snapshot.as_of_time.value,
                data_version="race-snapshot-v1",
                manifest=manifest,
                created_at=datetime.now(UTC),
            ),
        )
        self._session.flush()


class FeatureSnapshotRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, vector: FeatureVector) -> None:
        values = {
            "features": dict(vector.values),
            "source_observation_ids": list(vector.source_observation_ids),
            "missing_fields": list(vector.missing_fields),
        }
        self._session.add(
            FeatureSnapshot(
                feature_snapshot_id=vector.feature_snapshot_id,
                race_id=vector.race_id,
                horse_id=vector.runner_id,
                as_of_time=vector.as_of_time.value,
                data_snapshot_id=vector.data_snapshot_id,
                feature_version_id=vector.feature_version_id,
                logic_version_id=vector.logic_version_id,
                values=values,
                created_at=datetime.now(UTC),
            ),
        )
        self._session.flush()
