import hashlib
import json
import math
from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from keiba_domain.time_values import UtcInstant

from .errors import PredictionInvariantError, TrainingLeakError


def _checksum(value: Mapping[str, object]) -> str:
    serialized = json.dumps(dict(value), sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class TrainingExample:
    example_id: str
    race_id: str
    runner_id: str
    race_year: int
    feature_version_id: str
    features: Mapping[str, object]
    won: bool
    top2: bool
    top3: bool


@dataclass(frozen=True, slots=True)
class TrainingManifest:
    manifest_id: str
    test_year: int
    training_years: tuple[int, ...]
    training_example_ids: tuple[str, ...]
    feature_version_id: str
    model_version_id: str
    logic_version_id: str
    checksum: str

    @classmethod
    def create(
        cls,
        *,
        manifest_id: str,
        test_year: int,
        training_years: Iterable[int],
        examples: Iterable[TrainingExample],
        feature_version_id: str,
        model_version_id: str,
        logic_version_id: str,
    ) -> "TrainingManifest":
        years = tuple(training_years)
        expected_years = tuple(range(2019, test_year))
        if test_year < 2022 or years != expected_years:
            raise TrainingLeakError(
                "training years must be the contiguous 2019..test_year-1 window "
                "with test_year at least 2022",
            )

        rows = tuple(examples)
        if not rows:
            raise TrainingLeakError("training examples cannot be empty")
        example_ids = tuple(sorted(row.example_id for row in rows))
        if len(set(example_ids)) != len(example_ids):
            raise TrainingLeakError("training example IDs must be unique")
        expected_year_set = set(expected_years)
        row_years = {row.race_year for row in rows}
        if row_years != expected_year_set:
            raise TrainingLeakError("every training year must have at least one example")
        if any(row.race_year >= test_year for row in rows):
            raise TrainingLeakError("training example belongs to the test period")
        if any(row.feature_version_id != feature_version_id for row in rows):
            raise TrainingLeakError("training example feature version mismatch")

        canonical = {
            "manifest_id": manifest_id,
            "test_year": test_year,
            "training_years": years,
            "training_example_ids": example_ids,
            "feature_version_id": feature_version_id,
            "model_version_id": model_version_id,
            "logic_version_id": logic_version_id,
        }
        return cls(
            manifest_id=manifest_id,
            test_year=test_year,
            training_years=years,
            training_example_ids=example_ids,
            feature_version_id=feature_version_id,
            model_version_id=model_version_id,
            logic_version_id=logic_version_id,
            checksum=_checksum(canonical),
        )


def _validate_probability(name: str, value: float) -> None:
    if not 0.0 <= value <= 1.0:
        raise PredictionInvariantError(f"{name} must be between 0 and 1")


@dataclass(frozen=True, slots=True)
class RunnerPrediction:
    runner_id: str
    raw_win_probability: float
    win_probability: float
    raw_top2_probability: float
    top2_probability: float
    raw_top3_probability: float
    top3_probability: float
    ranking_score: float
    uncertainty: float
    disagreement: float

    def __post_init__(self) -> None:
        probability_fields = (
            "raw_win_probability",
            "win_probability",
            "raw_top2_probability",
            "top2_probability",
            "raw_top3_probability",
            "top3_probability",
        )
        for field_name in probability_fields:
            _validate_probability(field_name, getattr(self, field_name))
        if self.win_probability > self.top2_probability:
            raise PredictionInvariantError("win probability cannot exceed top-2 probability")
        if self.top2_probability > self.top3_probability:
            raise PredictionInvariantError("top-2 probability cannot exceed top-3 probability")
        if self.raw_win_probability > self.raw_top2_probability:
            raise PredictionInvariantError(
                "raw win probability cannot exceed raw top-2 probability",
            )
        if self.raw_top2_probability > self.raw_top3_probability:
            raise PredictionInvariantError(
                "raw top-2 probability cannot exceed raw top-3 probability",
            )
        _validate_probability("uncertainty", self.uncertainty)
        _validate_probability("disagreement", self.disagreement)


@dataclass(frozen=True, slots=True)
class PredictionSnapshot:
    prediction_snapshot_id: str
    race_id: str
    as_of_time: UtcInstant
    data_snapshot_id: str
    feature_version_id: str
    model_version_id: str
    logic_version_id: str
    training_manifest_id: str
    model_manifest_checksum: str
    calibration_version_id: str | None
    predictions: tuple[RunnerPrediction, ...]

    def __post_init__(self) -> None:
        if not self.predictions:
            raise PredictionInvariantError("prediction snapshot requires at least one runner")
        runner_ids = tuple(prediction.runner_id for prediction in self.predictions)
        if len(set(runner_ids)) != len(runner_ids):
            raise PredictionInvariantError("prediction runner IDs must be unique")
        win_total = math.fsum(prediction.win_probability for prediction in self.predictions)
        if not math.isclose(win_total, 1.0, rel_tol=0.0, abs_tol=1e-9):
            raise PredictionInvariantError("race win probabilities must sum to 1")
