from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping
from dataclasses import dataclass

from .errors import PredictionInvariantError


def _checksum(value: object) -> str:
    serialized = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class PersistedPrediction:
    prediction_snapshot_id: str
    race_id: str
    probabilities: Mapping[str, float]
    model_version_id: str

    def __post_init__(self) -> None:
        if not self.prediction_snapshot_id or not self.race_id or not self.model_version_id:
            raise PredictionInvariantError("persisted prediction lineage is incomplete")
        if not self.probabilities or any(
            not 0.0 <= probability <= 1.0 for probability in self.probabilities.values()
        ):
            raise PredictionInvariantError("persisted prediction probabilities are invalid")
        if not math.isclose(math.fsum(self.probabilities.values()), 1.0, abs_tol=1e-9):
            raise PredictionInvariantError("persisted prediction probabilities must sum to 1")


@dataclass(frozen=True, slots=True)
class PolicyReplayResult:
    replay_id: str
    race_id: str
    prediction_snapshot_id: str
    prediction_checksum: str
    policy_version_id: str
    decision: str
    selected_runner_id: str | None
    allocation_yen: int


class PolicyReplay:
    def __init__(self, *, policy_version_id: str, starting_capital_yen: int) -> None:
        self._policy_version_id = policy_version_id
        self._starting_capital_yen = starting_capital_yen

    def replay(
        self,
        prediction: PersistedPrediction,
        *,
        odds: Mapping[str, float],
    ) -> PolicyReplayResult:
        expected_value = {
            runner_id: prediction.probabilities[runner_id] * float(odds[runner_id]) - 1.0
            for runner_id in prediction.probabilities
            if runner_id in odds
        }
        if not expected_value:
            return PolicyReplayResult(
                replay_id=f"replay:{prediction.prediction_snapshot_id}:{self._policy_version_id}",
                race_id=prediction.race_id,
                prediction_snapshot_id=prediction.prediction_snapshot_id,
                prediction_checksum=_checksum(dict(prediction.probabilities)),
                policy_version_id=self._policy_version_id,
                decision="SKIP",
                selected_runner_id=None,
                allocation_yen=0,
            )
        selected_runner_id = max(expected_value, key=expected_value.__getitem__)
        best_ev = expected_value[selected_runner_id]
        if best_ev <= 0.0:
            decision = "SKIP"
            allocation_yen = 0
        else:
            decision = "BUY"
            runner_odds = float(odds[selected_runner_id])
            full_kelly = max(
                0.0,
                (prediction.probabilities[selected_runner_id] * runner_odds - 1.0)
                / (runner_odds - 1.0),
            )
            allocation_rate = min(full_kelly * 0.25, 0.03)
            allocation_yen = int(self._starting_capital_yen * allocation_rate // 100 * 100)
        return PolicyReplayResult(
            replay_id=f"replay:{prediction.prediction_snapshot_id}:{self._policy_version_id}",
            race_id=prediction.race_id,
            prediction_snapshot_id=prediction.prediction_snapshot_id,
            prediction_checksum=_checksum(dict(prediction.probabilities)),
            policy_version_id=self._policy_version_id,
            decision=decision,
            selected_runner_id=selected_runner_id,
            allocation_yen=allocation_yen,
        )


@dataclass(frozen=True, slots=True)
class EvaluationResult:
    prediction_metrics: dict[str, object]
    betting_metrics: dict[str, object] | None
    odds_coverage_status: str


class CoverageAwareEvaluator:
    @staticmethod
    def evaluate(
        *,
        prediction: PersistedPrediction,
        actual_winner: str,
        recommendation_decision: str,
        odds_coverage_status: str,
        payout_yen: int | None,
    ) -> EvaluationResult:
        top_runner = max(prediction.probabilities, key=prediction.probabilities.__getitem__)
        prediction_metrics: dict[str, object] = {
            "top1_runner_id": top_runner,
            "top1_correct": top_runner == actual_winner,
        }
        betting_metrics: dict[str, object] | None
        if odds_coverage_status != "complete":
            betting_metrics = None
        elif recommendation_decision == "BUY" and payout_yen is not None:
            betting_metrics = {"payout_yen": payout_yen, "profit_yen": payout_yen - 100}
        else:
            betting_metrics = {"payout_yen": 0, "profit_yen": 0}
        return EvaluationResult(
            prediction_metrics=prediction_metrics,
            betting_metrics=betting_metrics,
            odds_coverage_status=odds_coverage_status,
        )
