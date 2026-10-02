import hashlib
import json
from datetime import UTC, datetime
from typing import Any

from keiba_application.errors import (
    AppendOnlyViolationError,
    RecommendationNotPersistedError,
    ResultNotAvailableError,
)
from keiba_application.ports import ObservationRecord
from keiba_domain.time_values import UtcInstant
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from .schema import (
    BacktestArtifact,
    BacktestFold,
    BacktestGuardResult,
    BacktestRun,
    BetCandidate,
    CalculationArtifact,
    DataSnapshot,
    Evaluation,
    FeatureVersion,
    LogicTrace,
    LogicVersion,
    ModelVersion,
    OddsSnapshot,
    PredictionSnapshot,
    RawObservation,
    Recommendation,
    RecommendationItem,
    Result,
    Simulation,
    SimulationResult,
)


def _utc_datetime(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _utc_instant(value: datetime) -> UtcInstant:
    return UtcInstant.from_datetime(_utc_datetime(value))


def _payload_checksum(payload: dict[str, Any]) -> str:
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


class TemporalObservationRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(
        self,
        record: ObservationRecord,
        *,
        effective_to: UtcInstant | None = None,
        ingestion_batch_id: str | None = None,
    ) -> None:
        payload = dict(record.payload)
        effective_end = effective_to if effective_to is not None else record.effective_to
        self._session.add(
            RawObservation(
                observation_id=record.record_id,
                provider=record.source,
                provider_version=record.source_version,
                provider_record_type=record.provider_record_type,
                provider_record_key=record.provider_record_key,
                source_timestamp=record.source_timestamp.value,
                received_timestamp=record.received_timestamp.value,
                effective_from=record.effective_from.value,
                effective_to=effective_end.value if effective_end is not None else None,
                payload=payload,
                payload_checksum=_payload_checksum(payload),
                ingestion_batch_id=ingestion_batch_id or f"fixture:{record.source_version}",
                created_at=datetime.now(UTC),
            ),
        )
        self._session.flush()

    def eligible_as_of(self, as_of_time: UtcInstant) -> tuple[ObservationRecord, ...]:
        cutoff = as_of_time.value
        statement = (
            select(RawObservation)
            .where(
                and_(
                    RawObservation.received_timestamp <= cutoff,
                    RawObservation.effective_from <= cutoff,
                    or_(
                        RawObservation.effective_to.is_(None), RawObservation.effective_to > cutoff
                    ),
                ),
            )
            .order_by(RawObservation.observation_id)
        )
        rows = self._session.scalars(statement).all()
        return tuple(
            ObservationRecord(
                record_id=row.observation_id,
                source=row.provider,
                source_version=row.provider_version,
                source_timestamp=_utc_instant(row.source_timestamp),
                received_timestamp=_utc_instant(row.received_timestamp),
                effective_from=_utc_instant(row.effective_from),
                payload=row.payload,
                provider_record_type=row.provider_record_type,
                provider_record_key=row.provider_record_key,
                effective_to=_utc_instant(row.effective_to) if row.effective_to else None,
            )
            for row in rows
        )

    def update(self, *_: object, **__: object) -> None:
        raise AppendOnlyViolationError("raw_observations is append-only")

    def delete(self, *_: object, **__: object) -> None:
        raise AppendOnlyViolationError("raw_observations is append-only")


class RecommendationRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, recommendation: Recommendation) -> None:
        self._session.add(recommendation)
        self._session.flush()

    def update(self, *_: object, **__: object) -> None:
        raise AppendOnlyViolationError("recommendations is append-only")

    def delete(self, *_: object, **__: object) -> None:
        raise AppendOnlyViolationError("recommendations is append-only")


class ResultRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, result: Result) -> None:
        recommendation = self._session.get(Recommendation, result.recommendation_id)
        if recommendation is None:
            raise RecommendationNotPersistedError(
                f"recommendation {result.recommendation_id} is not persisted",
            )
        if recommendation.race_id != result.race_id:
            raise ValueError("result race_id must match recommendation race_id")
        self._session.add(result)
        self._session.flush()

    def reveal(self, *, race_id: str, recommendation_id: str) -> Result:
        recommendation = self._session.get(Recommendation, recommendation_id)
        if recommendation is None:
            raise RecommendationNotPersistedError(
                f"recommendation {recommendation_id} is not persisted",
            )
        if recommendation.race_id != race_id:
            raise ValueError("result race_id must match recommendation race_id")
        result = self._session.scalar(
            select(Result).where(
                Result.race_id == race_id,
                Result.recommendation_id == recommendation_id,
            ),
        )
        if result is None:
            raise ResultNotAvailableError(
                f"result for recommendation {recommendation_id} is not available",
            )
        return result


class GoldenRacePersistenceRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add_stage_artifact(self, artifact: object, *, stage_order: int) -> None:
        from keiba_application.golden_race import StageArtifact

        if not isinstance(artifact, StageArtifact):
            raise TypeError("artifact must be a StageArtifact")
        created_at = datetime.now(UTC)
        self._session.add(
            CalculationArtifact(
                artifact_id=artifact.artifact_id,
                run_id=artifact.run_id,
                race_id=artifact.race_id,
                stage=artifact.stage.value,
                output=artifact.output,
                lineage={
                    "data_snapshot_id": artifact.lineage.data_snapshot_id,
                    "feature_version_id": artifact.lineage.feature_version_id,
                    "model_version_id": artifact.lineage.model_version_id,
                    "logic_version_id": artifact.lineage.logic_version_id,
                    "input_ids": list(artifact.lineage.input_ids),
                },
                checksum=artifact.checksum,
                status=artifact.status,
                calculated_at=artifact.calculated_at.value,
                created_at=created_at,
            ),
        )
        self._session.flush()
        self._session.add(
            LogicTrace(
                trace_id=f"trace:{artifact.artifact_id}",
                run_id=artifact.run_id,
                race_id=artifact.race_id,
                stage=artifact.stage.value,
                stage_order=stage_order,
                artifact_ref_id=artifact.artifact_id,
                input_ids=list(artifact.lineage.input_ids),
                output=artifact.output,
                data_snapshot_id=artifact.lineage.data_snapshot_id,
                feature_version_id=artifact.lineage.feature_version_id,
                model_version_id=artifact.lineage.model_version_id,
                logic_version_id=artifact.lineage.logic_version_id,
                status=artifact.status,
                error=artifact.error,
                calculated_at=artifact.calculated_at.value,
                duration_ms=0.0,
                created_at=created_at,
            ),
        )
        self._session.flush()

    def persist_pipeline_result(self, result: object, *, case: object, config: object) -> str:
        from keiba_application.golden_race import (
            GOLDEN_STAGE_ORDER,
            GoldenRaceCase,
            PipelineConfig,
            PipelineResult,
        )

        if not isinstance(result, PipelineResult) or not isinstance(case, GoldenRaceCase):
            raise TypeError("result and case must be Golden Race contracts")
        if not isinstance(config, PipelineConfig):
            raise TypeError("config must be a PipelineConfig")
        if result.status != "succeeded" or result.decision is None:
            raise ValueError("only a succeeded pipeline result can be persisted")

        now = datetime.now(UTC)
        if self._session.get(ModelVersion, config.model_version_id) is None:
            self._session.add(
                ModelVersion(
                    version_id=config.model_version_id,
                    model_name="golden-fixture",
                    manifest={"run_id": config.run_id},
                    created_at=now,
                ),
            )
        if self._session.get(FeatureVersion, config.feature_version_id) is None:
            self._session.add(
                FeatureVersion(
                    version_id=config.feature_version_id,
                    feature_name="golden-fixture",
                    manifest={"run_id": config.run_id},
                    created_at=now,
                ),
            )
        if self._session.get(LogicVersion, config.logic_version_id) is None:
            self._session.add(
                LogicVersion(
                    version_id=config.logic_version_id,
                    logic_id=config.logic_version_id.split("-v", maxsplit=1)[0],
                    manifest={"run_id": config.run_id},
                    created_at=now,
                ),
            )
        if self._session.get(DataSnapshot, config.data_snapshot_id) is None:
            self._session.add(
                DataSnapshot(
                    snapshot_id=config.data_snapshot_id,
                    as_of_time=case.as_of_time.value,
                    data_version="golden-fixture-v2",
                    manifest={"run_id": config.run_id, "race_id": case.race_id},
                    created_at=now,
                ),
            )
        self._session.flush()

        prediction_artifact = next(
            artifact for artifact in result.artifacts if artifact.stage.value == "prediction"
        )
        prediction_id = f"prediction:{config.run_id}:{case.race_id}"
        if self._session.get(PredictionSnapshot, prediction_id) is None:
            self._session.add(
                PredictionSnapshot(
                    prediction_snapshot_id=prediction_id,
                    race_id=case.race_id,
                    as_of_time=case.as_of_time.value,
                    data_snapshot_id=config.data_snapshot_id,
                    feature_version_id=config.feature_version_id,
                    model_version_id=config.model_version_id,
                    logic_version_id=config.logic_version_id,
                    predictions=prediction_artifact.output["win_probabilities"],
                    created_at=now,
                ),
            )
        self._session.flush()

        for stage_artifact in result.artifacts:
            self.add_stage_artifact(
                stage_artifact,
                stage_order=GOLDEN_STAGE_ORDER.index(stage_artifact.stage) + 1,
            )

        simulation_artifact = next(
            artifact for artifact in result.artifacts if artifact.stage.value == "simulation"
        )
        simulation_id = f"simulation:{config.run_id}:{case.race_id}"
        self._session.add(
            Simulation(
                simulation_id=simulation_id,
                run_id=config.run_id,
                race_id=case.race_id,
                seed=config.seed,
                logic_version_id=config.logic_version_id,
                payload=simulation_artifact.output,
                created_at=now,
            ),
        )
        self._session.flush()
        self._session.add(
            SimulationResult(
                simulation_result_id=f"simulation-result:{config.run_id}:{case.race_id}",
                simulation_id=simulation_id,
                payload=simulation_artifact.output,
                created_at=now,
            ),
        )

        odds_snapshot_id = f"odds:{config.run_id}:{case.race_id}"
        self._session.add(
            OddsSnapshot(
                odds_snapshot_id=odds_snapshot_id,
                race_id=case.race_id,
                received_at=case.odds_received_at.value,
                as_of_time=case.odds_snapshot_time.value,
                coverage_status="complete",
                odds=case.odds,
                data_snapshot_id=config.data_snapshot_id,
                logic_version_id=config.logic_version_id,
                created_at=now,
            ),
        )
        self._session.flush()

        prediction_probabilities = prediction_artifact.output["win_probabilities"]
        ev_artifact = next(
            artifact for artifact in result.artifacts if artifact.stage.value == "ev"
        )
        ev_values = ev_artifact.output["win_ev"]
        raw_win_odds = case.odds["win"]
        if not isinstance(prediction_probabilities, dict) or not isinstance(ev_values, dict):
            raise ValueError("prediction and EV artifacts must contain mappings")
        if not isinstance(raw_win_odds, dict) or result.selected_runner_id is None:
            raise ValueError("Golden Race result must have selected runner and odds")
        candidate_id = f"candidate:{config.run_id}:{case.race_id}"
        self._session.add(
            BetCandidate(
                candidate_id=candidate_id,
                race_id=case.race_id,
                prediction_snapshot_id=prediction_id,
                odds_snapshot_id=odds_snapshot_id,
                bet_type="WIN",
                combination=result.selected_runner_id,
                model_probability=float(prediction_probabilities[result.selected_runner_id]),
                odds=float(raw_win_odds[result.selected_runner_id]),
                expected_value=float(ev_values[result.selected_runner_id]),
                uncertainty=0.0,
                logic_version_id=config.logic_version_id,
                payload={"source": "golden-race"},
                created_at=now,
            ),
        )
        self._session.flush()

        recommendation_id = f"recommendation:{config.run_id}:{case.race_id}"
        self._session.add(
            Recommendation(
                recommendation_id=recommendation_id,
                race_id=case.race_id,
                decision=result.decision.value,
                strategy="golden",
                data_snapshot_id=config.data_snapshot_id,
                prediction_snapshot_id=prediction_id,
                feature_version_id=config.feature_version_id,
                model_version_id=config.model_version_id,
                logic_version_id=config.logic_version_id,
                payload={
                    "reason": result.decision_reason,
                    "selected_runner_id": result.selected_runner_id,
                    "allocation_yen": result.allocation_yen,
                },
                persisted_at=now,
            ),
        )
        self._session.flush()
        if result.decision.value == "BUY":
            self._session.add(
                RecommendationItem(
                    recommendation_item_id=f"recommendation-item:{config.run_id}:{case.race_id}",
                    recommendation_id=recommendation_id,
                    candidate_id=candidate_id,
                    stake_yen=result.allocation_yen,
                    payload={"bet_type": "WIN"},
                    created_at=now,
                ),
            )
        self._session.flush()
        return recommendation_id

    def add_evaluation(self, evaluation: Evaluation) -> None:
        self._session.add(evaluation)
        self._session.flush()

    def update_stage_artifact(self, *_: object, **__: object) -> None:
        raise AppendOnlyViolationError("calculation_artifacts is append-only")

    def delete_stage_artifact(self, *_: object, **__: object) -> None:
        raise AppendOnlyViolationError("calculation_artifacts is append-only")


class BacktestPersistenceRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add_run(self, run: BacktestRun) -> None:
        self._session.add(run)
        self._session.flush()

    def add_fold(self, fold: BacktestFold) -> None:
        self._session.add(fold)
        self._session.flush()

    def add_guard_result(self, result: BacktestGuardResult) -> None:
        self._session.add(result)
        self._session.flush()

    def add_artifact(self, artifact: BacktestArtifact) -> None:
        self._session.add(artifact)
        self._session.flush()

    def update_run(self, *_: object, **__: object) -> None:
        raise AppendOnlyViolationError("backtest_runs is append-only")

    def delete_run(self, *_: object, **__: object) -> None:
        raise AppendOnlyViolationError("backtest_runs is append-only")

    def update_fold(self, *_: object, **__: object) -> None:
        raise AppendOnlyViolationError("backtest_folds is append-only")

    def delete_fold(self, *_: object, **__: object) -> None:
        raise AppendOnlyViolationError("backtest_folds is append-only")

    def update_guard_result(self, *_: object, **__: object) -> None:
        raise AppendOnlyViolationError("backtest_guard_results is append-only")

    def delete_guard_result(self, *_: object, **__: object) -> None:
        raise AppendOnlyViolationError("backtest_guard_results is append-only")

    def update_artifact(self, *_: object, **__: object) -> None:
        raise AppendOnlyViolationError("backtest_artifacts is append-only")

    def delete_artifact(self, *_: object, **__: object) -> None:
        raise AppendOnlyViolationError("backtest_artifacts is append-only")
