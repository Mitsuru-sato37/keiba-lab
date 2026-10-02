import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Literal, cast

from keiba_application.backtest_engine import BacktestInputProvider, BacktestRace
from keiba_application.ports import ObservationRecord
from keiba_application.predictions import TrainingExample
from keiba_application.snapshots import FeatureVector
from keiba_domain.time_values import UtcInstant

RecommendationDecision = Literal["BUY", "SKIP"]


@dataclass(frozen=True, slots=True)
class ExpectedRecommendation:
    race_id: str
    decision: RecommendationDecision
    skip_reason: str | None


@dataclass(frozen=True, slots=True)
class OneDayValidationFixture:
    fixture_version: str
    seed: int
    source: str
    target_date: date
    training_examples: tuple[TrainingExample, ...]
    races: tuple[BacktestRace, ...]
    expected_recommendations: Mapping[str, ExpectedRecommendation]
    checksum: str


def _mapping(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return cast(dict[str, object], value)


def _list(value: object, label: str) -> list[object]:
    if not isinstance(value, list):
        raise ValueError(f"{label} must be an array")
    return value


def _string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a non-empty string")
    return value


def _integer(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{label} must be an integer")
    return value


def _boolean(value: object, label: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{label} must be a boolean")
    return value


def _number(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a number")
    return float(value)


def _instant(value: object, label: str) -> UtcInstant:
    text = _string(value, label)
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as error:
        raise ValueError(f"{label} must be an ISO timestamp") from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{label} must include a timezone")
    return UtcInstant.from_datetime(parsed)


def _recommendation(value: object, race_id: str) -> ExpectedRecommendation:
    decision = _string(value, f"{race_id}.expected_decision")
    if decision not in {"BUY", "SKIP"}:
        raise ValueError(f"{race_id}.expected_decision must be BUY or SKIP")
    return ExpectedRecommendation(
        race_id=race_id,
        decision=cast(RecommendationDecision, decision),
        skip_reason=None,
    )


def _training_examples(raw_rows: object) -> tuple[TrainingExample, ...]:
    rows: list[TrainingExample] = []
    for index, raw_row in enumerate(_list(raw_rows, "training_examples")):
        row = _mapping(raw_row, f"training_examples[{index}]")
        rows.append(
            TrainingExample(
                example_id=_string(row.get("example_id"), f"training_examples[{index}].example_id"),
                race_id=_string(row.get("race_id"), f"training_examples[{index}].race_id"),
                runner_id=_string(row.get("runner_id"), f"training_examples[{index}].runner_id"),
                race_year=_integer(row.get("race_year"), f"training_examples[{index}].race_year"),
                feature_version_id=_string(
                    row.get("feature_version_id"),
                    f"training_examples[{index}].feature_version_id",
                ),
                features=_mapping(row.get("features"), f"training_examples[{index}].features"),
                won=_boolean(row.get("won"), f"training_examples[{index}].won"),
                top2=_boolean(row.get("top2"), f"training_examples[{index}].top2"),
                top3=_boolean(row.get("top3"), f"training_examples[{index}].top3"),
            ),
        )
    if tuple(row.race_year for row in rows) != (2019, 2020, 2021):
        raise ValueError("training examples must cover exactly 2019, 2020, and 2021")
    return tuple(rows)


def _race(
    raw_race: object,
    *,
    source: str,
    fixture_version: str,
) -> tuple[BacktestRace, ExpectedRecommendation]:
    race = _mapping(raw_race, "race")
    race_id = _string(race.get("race_id"), "race.race_id")
    as_of_time = _instant(race.get("as_of_time"), f"{race_id}.as_of_time")
    vectors: list[FeatureVector] = []
    observations: list[ObservationRecord] = []
    runners = _list(race.get("runner_features"), f"{race_id}.runner_features")
    for index, raw_runner in enumerate(runners):
        runner = _mapping(raw_runner, f"{race_id}.runner_features[{index}]")
        runner_id = _string(runner.get("runner_id"), f"{race_id}.runner_id")
        effective_at = _instant(
            runner.get("effective_at"),
            f"{race_id}.{runner_id}.effective_at",
        )
        values = _mapping(runner.get("values"), f"{race_id}.{runner_id}.values")
        observation_id = f"observation-{race_id}-{runner_id}"
        observations.append(
            ObservationRecord(
                record_id=observation_id,
                source=source,
                source_version=fixture_version,
                source_timestamp=effective_at,
                received_timestamp=effective_at,
                effective_from=effective_at,
                payload={
                    "race_id": race_id,
                    "runner_id": runner_id,
                    "features": values,
                },
                provider_record_type="runner",
            ),
        )
        vectors.append(
            FeatureVector(
                feature_snapshot_id=f"feature-{race_id}-{runner_id}",
                race_id=race_id,
                runner_id=runner_id,
                as_of_time=as_of_time,
                data_snapshot_id=f"snapshot-{race_id}",
                feature_version_id="core-feature-v1",
                logic_version_id="FEAT-001-v1",
                values=values,
                source_observation_ids=(observation_id,),
                missing_fields=(),
            ),
        )
    expected_decision = _recommendation(race.get("expected_decision"), race_id)
    skip_reason = race.get("expected_skip_reason")
    if skip_reason is not None:
        expected_decision = ExpectedRecommendation(
            race_id=race_id,
            decision=expected_decision.decision,
            skip_reason=_string(skip_reason, f"{race_id}.expected_skip_reason"),
        )
    result_payload = {
        "outcome": _mapping(race.get("outcome"), f"{race_id}.outcome"),
        "payouts": _mapping(race.get("payouts"), f"{race_id}.payouts"),
    }
    return (
        BacktestRace(
            race_id=race_id,
            test_year=2022,
            as_of_time=as_of_time,
            feature_vectors=tuple(vectors),
            observations=tuple(observations),
            result_payload=result_payload,
            odds_coverage=_number(race.get("odds_coverage"), f"{race_id}.odds_coverage"),
        ),
        expected_decision,
    )


def load_one_day_validation_fixture(path: Path) -> OneDayValidationFixture:
    raw_text = path.read_text(encoding="utf-8")
    raw = _mapping(json.loads(raw_text), "fixture")
    checksum_payload = json.dumps(
        raw,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    source = _string(raw.get("source"), "source")
    fixture_version = _string(raw.get("fixture_version"), "fixture_version")
    races_with_expectations = tuple(
        _race(item, source=source, fixture_version=fixture_version)
        for item in _list(raw.get("races"), "races")
    )
    ordered = tuple(
        sorted(
            races_with_expectations,
            key=lambda item: (item[0].as_of_time.value, item[0].race_id),
        ),
    )
    return OneDayValidationFixture(
        fixture_version=_string(raw.get("fixture_version"), "fixture_version"),
        seed=_integer(raw.get("seed"), "seed"),
        source=_string(raw.get("source"), "source"),
        target_date=date.fromisoformat(_string(raw.get("target_date"), "target_date")),
        training_examples=_training_examples(raw.get("training_examples")),
        races=tuple(item[0] for item in ordered),
        expected_recommendations={
            item[1].race_id: item[1]
            for item in ordered
        },
        checksum=hashlib.sha256(checksum_payload).hexdigest(),
    )


class OneDayValidationInputProvider(BacktestInputProvider):
    def __init__(self, fixture: OneDayValidationFixture) -> None:
        self._fixture = fixture

    def training_examples(self, years: tuple[int, ...]) -> tuple[TrainingExample, ...]:
        return tuple(
            example
            for example in self._fixture.training_examples
            if example.race_year in years
        )

    def races(self, test_year: int) -> tuple[BacktestRace, ...]:
        if test_year != 2022:
            raise ValueError("the one-day validation fixture supports test year 2022 only")
        return self._fixture.races
