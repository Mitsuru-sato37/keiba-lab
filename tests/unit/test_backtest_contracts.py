import pytest
from keiba_application.backtest import (
    BacktestManifest,
    BacktestRunResult,
    BacktestSpec,
    BacktestStatus,
    WalkForwardFold,
)
from keiba_application.errors import BacktestInvariantError


def make_spec(*, test_years: tuple[int, ...] = (2022, 2023, 2024, 2025)) -> BacktestSpec:
    return BacktestSpec.create(
        run_id="run-1",
        test_years=test_years,
        feature_version_id="core-feature-v1",
        model_version_id="baseline-gate-v1",
        logic_version_id="MODEL-BASE-001-v1",
        calibration_version_id=None,
        config_checksum="c" * 64,
        code_revision="revision-1",
        dependency_lock_checksum="d" * 64,
        random_seeds={"simulation": 7},
    )


def test_2022_fold_uses_only_2019_to_2021() -> None:
    fold = WalkForwardFold.create(test_year=2022)

    assert fold.fold_id == "fold-2022"
    assert fold.training_years == (2019, 2020, 2021)


def test_fold_rejects_test_year_before_2022() -> None:
    with pytest.raises(BacktestInvariantError, match="2022"):
        WalkForwardFold.create(test_year=2021)


def test_spec_accepts_contiguous_expanding_schedule() -> None:
    spec = make_spec()

    assert tuple(fold.test_year for fold in spec.folds) == (2022, 2023, 2024, 2025)
    assert spec.folds[1].training_years == (2019, 2020, 2021, 2022)
    assert len(spec.checksum) == 64


@pytest.mark.parametrize("test_years", [(2023,), (2022, 2024), (2022, 2023, 2023)])
def test_spec_rejects_schedule_that_does_not_start_at_2022_and_expand(
    test_years: tuple[int, ...],
) -> None:
    with pytest.raises(BacktestInvariantError, match="test years"):
        make_spec(test_years=test_years)


def test_spec_rejects_missing_required_version() -> None:
    with pytest.raises(BacktestInvariantError, match="version"):
        BacktestSpec.create(
            run_id="run-1",
            test_years=(2022,),
            feature_version_id="",
            model_version_id="baseline-gate-v1",
            logic_version_id="MODEL-BASE-001-v1",
            calibration_version_id=None,
            config_checksum="c" * 64,
            code_revision="revision-1",
            dependency_lock_checksum="d" * 64,
            random_seeds={"simulation": 7},
        )


def test_manifest_checksum_is_stable_for_reordered_input_ids() -> None:
    spec = make_spec(test_years=(2022,))
    first = BacktestManifest.create(
        spec,
        input_snapshot_ids=("snapshot-b", "snapshot-a"),
        training_example_ids=("example-b", "example-a"),
    )
    second = BacktestManifest.create(
        spec,
        input_snapshot_ids=("snapshot-a", "snapshot-b"),
        training_example_ids=("example-a", "example-b"),
    )

    assert first.checksum == second.checksum
    assert first.input_snapshot_ids == ("snapshot-a", "snapshot-b")


def test_invalid_run_result_cannot_expose_official_metrics() -> None:
    result = BacktestRunResult.invalid(
        run_id="run-1",
        guard_result_ids=("guard-1",),
        diagnostic="LEAK-002 failed",
    )

    assert result.status is BacktestStatus.INVALID
    assert result.official_metrics_available is False
    assert result.guard_result_ids == ("guard-1",)
    assert result.diagnostic == "LEAK-002 failed"
