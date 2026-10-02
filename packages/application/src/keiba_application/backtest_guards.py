import hashlib
import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from keiba_domain.time_values import UtcInstant

from .backtest import GuardResult, WalkForwardFold
from .errors import GuardViolationError, ResultAccessDeniedError
from .ports import ObservationRecord
from .predictions import TrainingManifest

GUARD_VERSIONS = {
    "LEAK-001": "LEAK-001-v1",
    "LEAK-002": "LEAK-002-v1",
    "LEAK-003": "LEAK-003-v1",
    "LEAK-004": "LEAK-004-v1",
    "VERSION-001": "VERSION-001-v1",
}
_ACCESS_SECRET = object()


def _guard_result_id(guard_id: str, checked_input_ids: Iterable[str], details: object) -> str:
    payload = {
        "guard_id": guard_id,
        "checked_input_ids": tuple(sorted(checked_input_ids)),
        "details": details,
    }
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return f"guard-{hashlib.sha256(serialized.encode('utf-8')).hexdigest()[:24]}"


def _result(
    *,
    guard_id: str,
    passed: bool,
    checked_input_ids: Iterable[str],
    details: Mapping[str, object],
) -> GuardResult:
    checked = tuple(sorted(checked_input_ids))
    result_id = _guard_result_id(guard_id, checked, details)
    factory = GuardResult.passed if passed else GuardResult.failed
    return factory(
        guard_result_id=result_id,
        guard_id=guard_id,
        guard_version=GUARD_VERSIONS[guard_id],
        checked_input_ids=checked,
        details=details,
    )


def _contains_odds(value: object) -> bool:
    if isinstance(value, ObservationRecord):
        return value.provider_record_type.lower() == "odds" or _contains_odds(value.payload)
    if isinstance(value, Mapping):
        for key, nested in value.items():
            if "odds" in str(key).lower():
                return True
            if _contains_odds(nested):
                return True
        return False
    if isinstance(value, (tuple, list, set, frozenset)):
        return any(_contains_odds(item) for item in value)
    nested_values = getattr(value, "values", None)
    return (
        nested_values is not None
        and nested_values is not value
        and _contains_odds(nested_values)
    )


class BacktestGuards:
    @staticmethod
    def check_temporal_eligibility(
        records: Iterable[ObservationRecord],
        as_of_time: UtcInstant,
    ) -> GuardResult:
        rows = tuple(records)
        checked_ids = tuple(row.record_id for row in rows)
        failures: list[str] = []
        for row in rows:
            if row.received_timestamp.value > as_of_time.value:
                failures.append(f"{row.record_id}:received_timestamp")
            if row.effective_from.value > as_of_time.value:
                failures.append(f"{row.record_id}:effective_from")
            if row.effective_to is not None and row.effective_to.value <= as_of_time.value:
                failures.append(f"{row.record_id}:effective_to")
        return _result(
            guard_id="LEAK-001",
            passed=not failures,
            checked_input_ids=checked_ids,
            details={"as_of_time": as_of_time.value.isoformat(), "failures": failures},
        )

    @staticmethod
    def check_training_window(
        manifest: TrainingManifest,
        fold: WalkForwardFold,
    ) -> GuardResult:
        failures: list[str] = []
        if manifest.test_year != fold.test_year:
            failures.append("test_year")
        if manifest.training_years != fold.training_years:
            failures.append("training_years")
        return _result(
            guard_id="LEAK-002",
            passed=not failures,
            checked_input_ids=manifest.training_example_ids,
            details={"failures": failures, "test_year": manifest.test_year},
        )

    @staticmethod
    def check_ability_inputs(inputs: Iterable[object]) -> GuardResult:
        values = tuple(inputs)
        checked_ids = tuple(
            value.record_id if isinstance(value, ObservationRecord) else f"input-{index}"
            for index, value in enumerate(values)
        )
        contains_odds = _contains_odds(values)
        return _result(
            guard_id="LEAK-003",
            passed=not contains_odds,
            checked_input_ids=checked_ids,
            details={"contains_odds": contains_odds},
        )

    @staticmethod
    def check_versions(
        *,
        required_versions: Mapping[str, str | None],
        artifact_versions: Mapping[str, str | None],
    ) -> GuardResult:
        failures: list[str] = []
        for name, required in required_versions.items():
            if required is None:
                continue
            if not required or artifact_versions.get(name) != required:
                failures.append(name)
        return _result(
            guard_id="VERSION-001",
            passed=not failures,
            checked_input_ids=tuple(required_versions),
            details={"failures": failures},
        )

    @staticmethod
    def require_pass(results: Iterable[GuardResult]) -> None:
        failed = tuple(result for result in results if result.status.value != "pass")
        if failed:
            guard_ids = ", ".join(result.guard_id for result in failed)
            raise GuardViolationError(f"backtest guards failed: {guard_ids}")


@dataclass(frozen=True, slots=True)
class ResultAccessCapability:
    _race_id: str
    _token: object

    @classmethod
    def _issue(cls, race_id: str) -> "ResultAccessCapability":
        return cls(_race_id=race_id, _token=_ACCESS_SECRET)

    def allows(self, race_id: str) -> bool:
        return bool(race_id) and race_id == self._race_id and self._token is _ACCESS_SECRET


class RecommendationPersistenceGate:
    @staticmethod
    def issue(
        *,
        race_id: str,
        recommendation_ids: Iterable[str],
        persisted_ids: Iterable[str],
    ) -> ResultAccessCapability:
        requested = tuple(sorted(set(recommendation_ids)))
        persisted = set(persisted_ids)
        if not race_id or not requested or not set(requested).issubset(persisted):
            raise ResultAccessDeniedError(
                "all recommendations for a race must be persisted before result access",
            )
        return ResultAccessCapability._issue(race_id)
