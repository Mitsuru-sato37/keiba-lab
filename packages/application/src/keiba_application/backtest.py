import hashlib
import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import StrEnum

from .errors import BacktestInvariantError


def _checksum(value: Mapping[str, object]) -> str:
    serialized = json.dumps(dict(value), sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


class BacktestStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    INVALID = "invalid"


class GuardStatus(StrEnum):
    PASS = "pass"
    FAIL = "fail"


@dataclass(frozen=True, slots=True)
class WalkForwardFold:
    fold_id: str
    test_year: int
    training_years: tuple[int, ...]

    @classmethod
    def create(cls, *, test_year: int, fold_id: str | None = None) -> "WalkForwardFold":
        if test_year < 2022:
            raise BacktestInvariantError("the first test year is 2022")
        resolved_fold_id = fold_id or f"fold-{test_year}"
        if not resolved_fold_id:
            raise BacktestInvariantError("fold_id is required")
        return cls(
            fold_id=resolved_fold_id,
            test_year=test_year,
            training_years=tuple(range(2019, test_year)),
        )


@dataclass(frozen=True, slots=True)
class BacktestSpec:
    run_id: str
    folds: tuple[WalkForwardFold, ...]
    feature_version_id: str
    model_version_id: str
    logic_version_id: str
    calibration_version_id: str | None
    config_checksum: str
    code_revision: str
    dependency_lock_checksum: str
    random_seeds: tuple[tuple[str, int], ...]
    checksum: str

    @classmethod
    def create(
        cls,
        *,
        run_id: str,
        test_years: Iterable[int],
        feature_version_id: str,
        model_version_id: str,
        logic_version_id: str,
        calibration_version_id: str | None,
        config_checksum: str,
        code_revision: str,
        dependency_lock_checksum: str,
        random_seeds: Mapping[str, int],
    ) -> "BacktestSpec":
        if not run_id:
            raise BacktestInvariantError("run_id is required")
        years = tuple(test_years)
        if not years or years != tuple(range(2022, years[-1] + 1)) or years[-1] > 2025:
            raise BacktestInvariantError("test years must start at 2022 and expand contiguously")
        required_versions = (feature_version_id, model_version_id, logic_version_id)
        if any(not version_id for version_id in required_versions):
            raise BacktestInvariantError("required version IDs must be present")
        if not config_checksum or not code_revision or not dependency_lock_checksum:
            raise BacktestInvariantError("configuration, code, and dependency lineage is required")
        seed_items = tuple(sorted((name, seed) for name, seed in random_seeds.items()))
        if not seed_items or any(
            not name or not isinstance(seed, int) for name, seed in seed_items
        ):
            raise BacktestInvariantError("random seeds must have names and integer values")
        folds = tuple(WalkForwardFold.create(test_year=year) for year in years)
        canonical = {
            "run_id": run_id,
            "folds": [
                {
                    "fold_id": fold.fold_id,
                    "test_year": fold.test_year,
                    "training_years": fold.training_years,
                }
                for fold in folds
            ],
            "feature_version_id": feature_version_id,
            "model_version_id": model_version_id,
            "logic_version_id": logic_version_id,
            "calibration_version_id": calibration_version_id,
            "config_checksum": config_checksum,
            "code_revision": code_revision,
            "dependency_lock_checksum": dependency_lock_checksum,
            "random_seeds": seed_items,
        }
        return cls(
            run_id=run_id,
            folds=folds,
            feature_version_id=feature_version_id,
            model_version_id=model_version_id,
            logic_version_id=logic_version_id,
            calibration_version_id=calibration_version_id,
            config_checksum=config_checksum,
            code_revision=code_revision,
            dependency_lock_checksum=dependency_lock_checksum,
            random_seeds=seed_items,
            checksum=_checksum(canonical),
        )


@dataclass(frozen=True, slots=True)
class BacktestManifest:
    run_id: str
    spec_checksum: str
    input_snapshot_ids: tuple[str, ...]
    training_example_ids: tuple[str, ...]
    checksum: str

    @classmethod
    def create(
        cls,
        spec: BacktestSpec,
        *,
        input_snapshot_ids: Iterable[str],
        training_example_ids: Iterable[str],
    ) -> "BacktestManifest":
        snapshot_ids = tuple(sorted(input_snapshot_ids))
        example_ids = tuple(sorted(training_example_ids))
        if any(not value for value in (*snapshot_ids, *example_ids)):
            raise BacktestInvariantError("manifest artifact IDs must be nonempty")
        canonical = {
            "run_id": spec.run_id,
            "spec_checksum": spec.checksum,
            "input_snapshot_ids": snapshot_ids,
            "training_example_ids": example_ids,
        }
        return cls(
            run_id=spec.run_id,
            spec_checksum=spec.checksum,
            input_snapshot_ids=snapshot_ids,
            training_example_ids=example_ids,
            checksum=_checksum(canonical),
        )


@dataclass(frozen=True, slots=True)
class GuardResult:
    guard_result_id: str
    guard_id: str
    guard_version: str
    status: GuardStatus
    checked_input_ids: tuple[str, ...]
    details: Mapping[str, object]

    @classmethod
    def passed(
        cls,
        *,
        guard_result_id: str,
        guard_id: str,
        guard_version: str,
        checked_input_ids: Iterable[str] = (),
        details: Mapping[str, object] | None = None,
    ) -> "GuardResult":
        return cls(
            guard_result_id=guard_result_id,
            guard_id=guard_id,
            guard_version=guard_version,
            status=GuardStatus.PASS,
            checked_input_ids=tuple(sorted(checked_input_ids)),
            details=dict(details or {}),
        )

    @classmethod
    def failed(
        cls,
        *,
        guard_result_id: str,
        guard_id: str,
        guard_version: str,
        checked_input_ids: Iterable[str] = (),
        details: Mapping[str, object] | None = None,
    ) -> "GuardResult":
        return cls(
            guard_result_id=guard_result_id,
            guard_id=guard_id,
            guard_version=guard_version,
            status=GuardStatus.FAIL,
            checked_input_ids=tuple(sorted(checked_input_ids)),
            details=dict(details or {}),
        )


@dataclass(frozen=True, slots=True)
class FoldManifest:
    fold_id: str
    test_year: int
    training_years: tuple[int, ...]
    training_example_ids: tuple[str, ...]
    checksum: str


@dataclass(frozen=True, slots=True)
class BacktestRunResult:
    run_id: str
    status: BacktestStatus
    fold_ids: tuple[str, ...]
    guard_result_ids: tuple[str, ...]
    artifact_ids: tuple[str, ...]
    official_metrics_available: bool
    diagnostic: str | None

    @classmethod
    def invalid(
        cls,
        *,
        run_id: str,
        guard_result_ids: Iterable[str],
        diagnostic: str,
    ) -> "BacktestRunResult":
        return cls(
            run_id=run_id,
            status=BacktestStatus.INVALID,
            fold_ids=(),
            guard_result_ids=tuple(guard_result_ids),
            artifact_ids=(),
            official_metrics_available=False,
            diagnostic=diagnostic,
        )
