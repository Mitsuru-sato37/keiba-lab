import hashlib
import json
import math
from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from keiba_application.errors import OddsLeakError, PredictionInvariantError, TrainingLeakError
from keiba_application.predictions import (
    PredictionSnapshot,
    RunnerPrediction,
    TrainingExample,
    TrainingManifest,
)
from keiba_application.snapshots import FeatureVector

BASELINE_MODEL_VERSION_ID = "baseline-gate-v1"
BASELINE_LOGIC_VERSION_ID = "MODEL-BASE-001-v1"


def _has_odds(values: Mapping[str, object]) -> bool:
    return any("odds" in key.lower() for key in values)


def _checksum(value: Mapping[str, object]) -> str:
    serialized = json.dumps(dict(value), sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _usable_gate(values: Mapping[str, object]) -> int | None:
    gate = values.get("runner.gate")
    if isinstance(gate, bool) or not isinstance(gate, int) or gate <= 0:
        return None
    return gate


@dataclass(frozen=True, slots=True)
class TrainedGateStrengthBaseline:
    training_manifest: TrainingManifest
    gate_scores: Mapping[int, float]
    gate_starts: Mapping[int, int]
    overall_score: float
    model_manifest_checksum: str
    model_version_id: str
    logic_version_id: str

    def predict(self, feature_vectors: Iterable[FeatureVector]) -> PredictionSnapshot:
        vectors = tuple(feature_vectors)
        if not vectors:
            raise PredictionInvariantError("prediction requires at least one feature vector")

        first = vectors[0]
        context = (
            first.race_id,
            first.data_snapshot_id,
            first.as_of_time,
            first.feature_version_id,
        )
        if first.feature_version_id != self.training_manifest.feature_version_id:
            raise PredictionInvariantError("feature context version does not match training manifest")

        runner_ids = tuple(vector.runner_id for vector in vectors)
        if len(set(runner_ids)) != len(runner_ids):
            raise PredictionInvariantError("prediction runner IDs must be unique")

        for vector in vectors:
            vector_context = (
                vector.race_id,
                vector.data_snapshot_id,
                vector.as_of_time,
                vector.feature_version_id,
            )
            if vector_context != context:
                raise PredictionInvariantError("feature vectors must share one prediction context")
            if vector.feature_version_id != self.training_manifest.feature_version_id:
                raise PredictionInvariantError(
                    "feature context version does not match training manifest",
                )
            if _has_odds(vector.values):
                raise OddsLeakError("current-race odds cannot enter ability prediction")

        scored: list[tuple[FeatureVector, float, float]] = []
        for vector in vectors:
            gate = _usable_gate(vector.values)
            if gate is None or gate not in self.gate_scores:
                score = self.overall_score
                uncertainty = 1.0
            else:
                score = self.gate_scores[gate]
                uncertainty = 1.0 / math.sqrt(self.gate_starts[gate] + 1)
            scored.append((vector, score, uncertainty))

        score_total = math.fsum(score for _, score, _ in scored)
        if score_total <= 0:
            win_by_runner = {vector.runner_id: 1.0 / len(scored) for vector, _, _ in scored}
        else:
            win_by_runner = {
                vector.runner_id: score / score_total for vector, score, _ in scored
            }

        predictions: list[RunnerPrediction] = []
        runner_count = len(scored)
        for vector, score, uncertainty in sorted(scored, key=lambda item: item[0].runner_id):
            win_probability = win_by_runner[vector.runner_id]
            if runner_count == 1:
                top2_probability = 1.0
                top3_probability = 1.0
            else:
                top2_probability = min(
                    1.0,
                    win_probability
                    + (1.0 - win_probability) * 1 / (runner_count - 1),
                )
                top3_probability = min(
                    1.0,
                    win_probability
                    + (1.0 - win_probability) * 2 / (runner_count - 1),
                )
            predictions.append(
                RunnerPrediction(
                    runner_id=vector.runner_id,
                    raw_win_probability=win_probability,
                    win_probability=win_probability,
                    raw_top2_probability=top2_probability,
                    top2_probability=top2_probability,
                    raw_top3_probability=top3_probability,
                    top3_probability=top3_probability,
                    ranking_score=score,
                    uncertainty=uncertainty,
                    disagreement=0.0,
                ),
            )

        prediction_key = {
            "race_id": first.race_id,
            "as_of_time": first.as_of_time.value.isoformat(),
            "data_snapshot_id": first.data_snapshot_id,
            "feature_version_id": first.feature_version_id,
            "model_version_id": self.model_version_id,
            "training_manifest_checksum": self.training_manifest.checksum,
        }
        prediction_snapshot_id = f"prediction-{_checksum(prediction_key)[:24]}"
        return PredictionSnapshot(
            prediction_snapshot_id=prediction_snapshot_id,
            race_id=first.race_id,
            as_of_time=first.as_of_time,
            data_snapshot_id=first.data_snapshot_id,
            feature_version_id=first.feature_version_id,
            model_version_id=self.model_version_id,
            logic_version_id=self.logic_version_id,
            training_manifest_id=self.training_manifest.manifest_id,
            model_manifest_checksum=self.model_manifest_checksum,
            calibration_version_id=None,
            predictions=tuple(predictions),
        )


class GateStrengthBaseline:
    @classmethod
    def fit(
        cls,
        *,
        manifest: TrainingManifest,
        examples: Iterable[TrainingExample],
    ) -> TrainedGateStrengthBaseline:
        rows = tuple(examples)
        row_ids = tuple(sorted(row.example_id for row in rows))
        if row_ids != manifest.training_example_ids:
            raise TrainingLeakError("fit examples must match the training manifest")
        if any(row.feature_version_id != manifest.feature_version_id for row in rows):
            raise TrainingLeakError("fit example feature version mismatch")
        if any(_has_odds(row.features) for row in rows):
            raise OddsLeakError("odds cannot enter ability model training")

        gate_starts: dict[int, int] = {}
        gate_wins: dict[int, int] = {}
        total_starts = len(rows)
        total_wins = sum(1 for row in rows if row.won)
        for row in rows:
            gate = _usable_gate(row.features)
            if gate is None:
                continue
            gate_starts[gate] = gate_starts.get(gate, 0) + 1
            gate_wins[gate] = gate_wins.get(gate, 0) + int(row.won)

        overall_score = (total_wins + 1) / (total_starts + 2)
        gate_scores = {
            gate: (gate_wins[gate] + 1) / (starts + 2)
            for gate, starts in gate_starts.items()
        }
        model_manifest = {
            "model_version_id": BASELINE_MODEL_VERSION_ID,
            "logic_version_id": BASELINE_LOGIC_VERSION_ID,
            "training_manifest_id": manifest.manifest_id,
            "training_manifest_checksum": manifest.checksum,
            "overall_score": overall_score,
            "gate_scores": gate_scores,
            "gate_starts": gate_starts,
        }
        return TrainedGateStrengthBaseline(
            training_manifest=manifest,
            gate_scores=gate_scores,
            gate_starts=gate_starts,
            overall_score=overall_score,
            model_manifest_checksum=_checksum(model_manifest),
            model_version_id=BASELINE_MODEL_VERSION_ID,
            logic_version_id=BASELINE_LOGIC_VERSION_ID,
        )
