from __future__ import annotations

import hashlib
import json
import math
import random
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, Protocol

from keiba_domain.time_values import UtcInstant

from .errors import GuardViolationError, OddsLeakError, PredictionInvariantError, TemporalLeakError


class StageId(StrEnum):
    DATA_SNAPSHOT = "data_snapshot"
    FEATURE_SNAPSHOT = "feature_snapshot"
    PREDICTION = "prediction"
    CALIBRATION = "calibration"
    SIMULATION = "simulation"
    BET_PROBABILITY = "bet_probability"
    ODDS_SNAPSHOT = "odds_snapshot"
    EV = "ev"
    STRATEGY = "strategy"
    MONEY_ALLOCATION = "money_allocation"
    RECOMMENDATION = "recommendation"
    RESULT = "result"
    EVALUATION = "evaluation"


GOLDEN_STAGE_ORDER: tuple[StageId, ...] = (
    StageId.DATA_SNAPSHOT,
    StageId.FEATURE_SNAPSHOT,
    StageId.PREDICTION,
    StageId.CALIBRATION,
    StageId.SIMULATION,
    StageId.BET_PROBABILITY,
    StageId.ODDS_SNAPSHOT,
    StageId.EV,
    StageId.STRATEGY,
    StageId.MONEY_ALLOCATION,
    StageId.RECOMMENDATION,
    StageId.RESULT,
    StageId.EVALUATION,
)


class RecommendationDecision(StrEnum):
    BUY = "BUY"
    SKIP = "SKIP"


@dataclass(frozen=True, slots=True)
class Lineage:
    data_snapshot_id: str
    feature_version_id: str
    model_version_id: str
    logic_version_id: str
    input_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if not all(
            (
                self.data_snapshot_id,
                self.feature_version_id,
                self.model_version_id,
                self.logic_version_id,
            ),
        ):
            raise PredictionInvariantError("stage lineage requires all version identifiers")


@dataclass(frozen=True, slots=True)
class StageArtifact:
    artifact_id: str
    run_id: str
    race_id: str
    stage: StageId
    output: dict[str, object]
    lineage: Lineage
    calculated_at: UtcInstant
    status: str
    error: str | None
    checksum: str

    @classmethod
    def create(
        cls,
        *,
        artifact_id: str,
        run_id: str,
        race_id: str,
        stage: StageId,
        output: dict[str, object],
        lineage: Lineage,
        calculated_at: UtcInstant | None = None,
        status: str = "succeeded",
        error: str | None = None,
    ) -> StageArtifact:
        if status not in {"succeeded", "invalid", "failed"}:
            raise PredictionInvariantError(f"unsupported stage status: {status}")
        if status == "succeeded" and error is not None:
            raise PredictionInvariantError("succeeded stage cannot carry an error")
        canonical = {
            "artifact_id": artifact_id,
            "run_id": run_id,
            "race_id": race_id,
            "stage": stage.value,
            "output": output,
            "lineage": {
                "data_snapshot_id": lineage.data_snapshot_id,
                "feature_version_id": lineage.feature_version_id,
                "model_version_id": lineage.model_version_id,
                "logic_version_id": lineage.logic_version_id,
                "input_ids": lineage.input_ids,
            },
            "status": status,
            "error": error,
        }
        serialized = json.dumps(canonical, sort_keys=True, separators=(",", ":"), default=str)
        return cls(
            artifact_id=artifact_id,
            run_id=run_id,
            race_id=race_id,
            stage=stage,
            output=dict(output),
            lineage=lineage,
            calculated_at=calculated_at or UtcInstant.from_datetime(datetime.now(UTC)),
            status=status,
            error=error,
            checksum=hashlib.sha256(serialized.encode("utf-8")).hexdigest(),
        )


@dataclass(frozen=True, slots=True)
class RunnerFeature:
    runner_id: str
    effective_at: UtcInstant
    values: dict[str, object]


@dataclass(frozen=True, slots=True)
class GoldenRaceCase:
    case_id: str
    race_id: str
    as_of_time: UtcInstant
    odds_received_at: UtcInstant
    odds_snapshot_time: UtcInstant
    prediction_inputs: dict[str, object]
    runner_features: tuple[RunnerFeature, ...]
    odds: dict[str, object]
    outcome: dict[str, object]
    payouts: dict[str, object]
    expected_decision: RecommendationDecision
    expected_skip_reason: str | None

    def __post_init__(self) -> None:
        if self.odds_received_at.value > self.odds_snapshot_time.value:
            raise PredictionInvariantError("odds must be received before the odds snapshot")
        if any(
            feature.effective_at.value > self.as_of_time.value
            for feature in self.runner_features
        ):
            raise PredictionInvariantError("runner feature is not effective at the as-of time")
        if "odds" in self.prediction_inputs and self.prediction_inputs["odds"] is not None:
            raise OddsLeakError("current-race odds cannot enter prediction inputs")
        if self.expected_decision is RecommendationDecision.SKIP and not self.expected_skip_reason:
            raise PredictionInvariantError("SKIP requires an explicit reason")
        if self.expected_decision is RecommendationDecision.BUY and self.expected_skip_reason:
            raise PredictionInvariantError("BUY cannot carry a skip reason")


@dataclass(frozen=True, slots=True)
class GoldenRaceFixture:
    fixture_version: str
    seed: int
    source: str
    cases: tuple[GoldenRaceCase, ...]

    def __post_init__(self) -> None:
        if not self.fixture_version or self.seed < 0 or not self.cases:
            raise PredictionInvariantError("Golden Race fixture metadata is incomplete")


def _instant(value: Any) -> UtcInstant:
    if not isinstance(value, str):
        raise PredictionInvariantError("fixture timestamp must be an ISO string")
    return UtcInstant.from_datetime(datetime.fromisoformat(value))


def _mapping(value: Any, *, field_name: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise PredictionInvariantError(f"fixture field {field_name} must be an object")
    return dict(value)


def load_golden_race_fixture(path: Path) -> GoldenRaceFixture:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise PredictionInvariantError("Golden Race fixture root must be an object")
    cases: list[GoldenRaceCase] = []
    for raw_case in raw.get("cases", []):
        if not isinstance(raw_case, dict):
            raise PredictionInvariantError("Golden Race case must be an object")
        features = tuple(
            RunnerFeature(
                runner_id=str(feature["runner_id"]),
                effective_at=_instant(feature["effective_at"]),
                values=_mapping(feature["values"], field_name="runner feature values"),
            )
            for feature in raw_case["runner_features"]
        )
        cases.append(
            GoldenRaceCase(
                case_id=str(raw_case["case_id"]),
                race_id=str(raw_case["race_id"]),
                as_of_time=_instant(raw_case["as_of_time"]),
                odds_received_at=_instant(raw_case["odds_received_at"]),
                odds_snapshot_time=_instant(raw_case["odds_snapshot_time"]),
                prediction_inputs=_mapping(
                    raw_case["prediction_inputs"], field_name="prediction inputs"
                ),
                runner_features=features,
                odds=_mapping(raw_case["odds"], field_name="odds"),
                outcome=_mapping(raw_case["outcome"], field_name="outcome"),
                payouts=_mapping(raw_case["payouts"], field_name="payouts"),
                expected_decision=RecommendationDecision(str(raw_case["expected_decision"])),
                expected_skip_reason=(
                    str(raw_case["expected_skip_reason"])
                    if raw_case.get("expected_skip_reason") is not None
                    else None
                ),
            ),
        )
    return GoldenRaceFixture(
        fixture_version=str(raw["fixture_version"]),
        seed=int(raw["seed"]),
        source=str(raw["source"]),
        cases=tuple(cases),
    )


@dataclass(frozen=True, slots=True)
class PredictionInput:
    race_id: str
    as_of_time: UtcInstant
    prediction_inputs: dict[str, object]
    runner_features: tuple[RunnerFeature, ...]


class AbilityPredictor(Protocol):
    def predict(self, prediction_input: PredictionInput) -> dict[str, float]: ...


class FormScorePredictor:
    """Deterministic fixture predictor used until a production model is wired in."""

    def predict(self, prediction_input: PredictionInput) -> dict[str, float]:
        scores = {
            feature.runner_id: self._score(feature.values["form_score"])
            for feature in prediction_input.runner_features
        }
        total = math.fsum(scores.values())
        if total <= 0.0:
            raise PredictionInvariantError("fixture form scores must have a positive total")
        return {runner_id: score / total for runner_id, score in scores.items()}

    @staticmethod
    def _score(value: object) -> float:
        if not isinstance(value, (int, float)):
            raise PredictionInvariantError("fixture form score must be numeric")
        return float(value)


@dataclass(frozen=True, slots=True)
class PipelineConfig:
    run_id: str
    seed: int
    data_snapshot_id: str
    feature_version_id: str
    model_version_id: str
    logic_version_id: str
    starting_capital_yen: int
    max_allocation_rate: float = 0.03
    kelly_fraction: float = 0.25


@dataclass(frozen=True, slots=True)
class PipelineResult:
    run_id: str
    race_id: str
    status: str
    artifacts: tuple[StageArtifact, ...]
    decision: RecommendationDecision | None
    decision_reason: str | None
    selected_runner_id: str | None
    allocation_yen: int
    diagnostic: str


class GoldenRacePipeline:
    """Runs the deterministic calculation stages up to recommendation persistence."""

    def __init__(self, config: PipelineConfig) -> None:
        self._config = config

    @staticmethod
    def stage_order() -> tuple[StageId, ...]:
        return GOLDEN_STAGE_ORDER[:11]

    def run(
        self,
        case: GoldenRaceCase,
        *,
        predictor: AbilityPredictor | None = None,
    ) -> PipelineResult:
        try:
            self._validate_guards(case)
            ability_predictor = predictor or FormScorePredictor()
            artifacts: list[StageArtifact] = []

            data_artifact = self._artifact(
                artifacts,
                case,
                StageId.DATA_SNAPSHOT,
                {"as_of_time": case.as_of_time.value.isoformat()},
            )
            feature_artifact = self._artifact(
                artifacts,
                case,
                StageId.FEATURE_SNAPSHOT,
                {
                    "runner_features": {
                        feature.runner_id: feature.values for feature in case.runner_features
                    },
                },
                input_ids=(data_artifact.artifact_id,),
            )
            prediction_input = PredictionInput(
                race_id=case.race_id,
                as_of_time=case.as_of_time,
                prediction_inputs=dict(case.prediction_inputs),
                runner_features=case.runner_features,
            )
            predictions = dict(ability_predictor.predict(prediction_input))
            self._validate_predictions(case, predictions)
            prediction_artifact = self._artifact(
                artifacts,
                case,
                StageId.PREDICTION,
                {"win_probabilities": predictions},
                input_ids=(feature_artifact.artifact_id,),
            )
            calibration_artifact = self._artifact(
                artifacts,
                case,
                StageId.CALIBRATION,
                {"win_probabilities": predictions, "calibration_version": "identity-v1"},
                input_ids=(prediction_artifact.artifact_id,),
            )
            simulation = self._simulate(case, predictions)
            simulation_artifact = self._artifact(
                artifacts,
                case,
                StageId.SIMULATION,
                simulation,
                input_ids=(calibration_artifact.artifact_id,),
            )
            bet_probability_artifact = self._artifact(
                artifacts,
                case,
                StageId.BET_PROBABILITY,
                {"win_probabilities": predictions},
                input_ids=(simulation_artifact.artifact_id,),
            )
            odds_artifact = self._artifact(
                artifacts,
                case,
                StageId.ODDS_SNAPSHOT,
                {"odds": case.odds},
                input_ids=(bet_probability_artifact.artifact_id,),
            )
            odds_by_runner = self._win_odds(case)
            ev_by_runner = {
                runner_id: predictions[runner_id] * odds_by_runner[runner_id] - 1.0
                for runner_id in predictions
            }
            ev_artifact = self._artifact(
                artifacts,
                case,
                StageId.EV,
                {"win_ev": ev_by_runner},
                input_ids=(odds_artifact.artifact_id,),
            )
            selected_runner_id = max(ev_by_runner, key=ev_by_runner.__getitem__)
            best_ev = ev_by_runner[selected_runner_id]
            decision = (
                RecommendationDecision.BUY
                if best_ev > 0.0
                else RecommendationDecision.SKIP
            )
            decision_reason = None if decision is RecommendationDecision.BUY else "SKIP_NO_VALUE"
            strategy_artifact = self._artifact(
                artifacts,
                case,
                StageId.STRATEGY,
                {
                    "decision": decision.value,
                    "reason": decision_reason,
                    "selected_runner_id": selected_runner_id,
                    "best_ev": best_ev,
                },
                input_ids=(ev_artifact.artifact_id,),
            )
            allocation_yen = self._allocation(
                probability=predictions[selected_runner_id],
                odds=odds_by_runner[selected_runner_id],
                decision=decision,
            )
            money_artifact = self._artifact(
                artifacts,
                case,
                StageId.MONEY_ALLOCATION,
                {"allocation_yen": allocation_yen},
                input_ids=(strategy_artifact.artifact_id,),
            )
            self._artifact(
                artifacts,
                case,
                StageId.RECOMMENDATION,
                {
                    "decision": decision.value,
                    "reason": decision_reason,
                    "selected_runner_id": selected_runner_id,
                    "allocation_yen": allocation_yen,
                },
                input_ids=(money_artifact.artifact_id,),
            )
            return PipelineResult(
                run_id=self._config.run_id,
                race_id=case.race_id,
                status="succeeded",
                artifacts=tuple(artifacts),
                decision=decision,
                decision_reason=decision_reason,
                selected_runner_id=selected_runner_id,
                allocation_yen=allocation_yen,
                diagnostic="",
            )
        except (
            GuardViolationError,
            OddsLeakError,
            PredictionInvariantError,
            TemporalLeakError,
        ) as exc:
            return PipelineResult(
                run_id=self._config.run_id,
                race_id=case.race_id,
                status="invalid",
                artifacts=(),
                decision=None,
                decision_reason=None,
                selected_runner_id=None,
                allocation_yen=0,
                diagnostic=str(exc),
            )

    def _validate_guards(self, case: GoldenRaceCase) -> None:
        required_versions = {
            "data snapshot": self._config.data_snapshot_id,
            "feature": self._config.feature_version_id,
            "model": self._config.model_version_id,
            "logic": self._config.logic_version_id,
        }
        missing = [name for name, value in required_versions.items() if not value]
        if missing:
            raise GuardViolationError(f"version guard failed: missing {', '.join(missing)} version")
        if self._config.seed < 0 or self._config.starting_capital_yen < 0:
            raise GuardViolationError("run configuration contains an invalid seed or capital")
        if any(
            feature.effective_at.value > case.as_of_time.value
            for feature in case.runner_features
        ):
            raise TemporalLeakError("runner feature is after the race as-of time")
        if case.prediction_inputs.get("odds") is not None:
            raise OddsLeakError("current-race odds cannot enter prediction inputs")

    @staticmethod
    def _validate_predictions(case: GoldenRaceCase, predictions: dict[str, float]) -> None:
        expected_runner_ids = {feature.runner_id for feature in case.runner_features}
        if set(predictions) != expected_runner_ids:
            raise PredictionInvariantError("prediction runner IDs do not match feature runner IDs")
        if any(not 0.0 <= probability <= 1.0 for probability in predictions.values()):
            raise PredictionInvariantError("prediction probabilities must be between 0 and 1")
        if not math.isclose(math.fsum(predictions.values()), 1.0, rel_tol=0.0, abs_tol=1e-9):
            raise PredictionInvariantError("prediction probabilities must sum to 1")

    @staticmethod
    def _win_odds(case: GoldenRaceCase) -> dict[str, float]:
        raw_odds = case.odds.get("win")
        if not isinstance(raw_odds, dict):
            raise PredictionInvariantError("fixture must include win odds for every runner")
        odds: dict[str, float] = {}
        for runner_id, value in raw_odds.items():
            if not isinstance(value, (int, float)):
                raise PredictionInvariantError("win odds must be numeric")
            odds[str(runner_id)] = float(value)
        if any(value <= 1.0 for value in odds.values()):
            raise PredictionInvariantError("win odds must be greater than 1")
        return odds

    def _simulate(self, case: GoldenRaceCase, predictions: dict[str, float]) -> dict[str, object]:
        random_source = random.Random(self._config.seed)
        draws = {runner_id: round(random_source.random(), 12) for runner_id in predictions}
        return {
            "seed": self._config.seed,
            "iterations": 1000,
            "runner_draws": draws,
            "race_id": case.race_id,
        }

    def _allocation(
        self,
        *,
        probability: float,
        odds: float,
        decision: RecommendationDecision,
    ) -> int:
        if decision is RecommendationDecision.SKIP:
            return 0
        full_kelly = max(0.0, (probability * odds - 1.0) / (odds - 1.0))
        capped_rate = min(
            full_kelly * self._config.kelly_fraction,
            self._config.max_allocation_rate,
        )
        raw_yen = self._config.starting_capital_yen * capped_rate
        return int(raw_yen // 100 * 100)

    def _artifact(
        self,
        artifacts: list[StageArtifact],
        case: GoldenRaceCase,
        stage: StageId,
        output: dict[str, object],
        *,
        input_ids: tuple[str, ...] = (),
    ) -> StageArtifact:
        artifact = StageArtifact.create(
            artifact_id=f"{self._config.run_id}:{case.race_id}:{stage.value}",
            run_id=self._config.run_id,
            race_id=case.race_id,
            stage=stage,
            output=output,
            lineage=Lineage(
                data_snapshot_id=self._config.data_snapshot_id,
                feature_version_id=self._config.feature_version_id,
                model_version_id=self._config.model_version_id,
                logic_version_id=self._config.logic_version_id,
                input_ids=input_ids,
            ),
        )
        artifacts.append(artifact)
        return artifact
