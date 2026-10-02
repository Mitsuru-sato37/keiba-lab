from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal, Protocol

from keiba_domain.time_values import UtcInstant

from .backtest import (
    BacktestRunResult,
    BacktestSpec,
    BacktestStatus,
    GuardResult,
)
from .backtest_guards import BacktestGuards, RecommendationPersistenceGate
from .errors import GuardViolationError, ResultAccessDeniedError
from .ports import ObservationRecord
from .predictions import PredictionSnapshot, TrainingExample, TrainingManifest
from .snapshots import FeatureVector


@dataclass(frozen=True, slots=True)
class BacktestRace:
    race_id: str
    test_year: int
    as_of_time: UtcInstant
    feature_vectors: tuple[FeatureVector, ...]
    observations: tuple[ObservationRecord, ...]
    result_payload: Mapping[str, object]
    odds_coverage: float


@dataclass(frozen=True, slots=True)
class RecommendationArtifact:
    recommendation_id: str
    race_id: str
    prediction_snapshot_id: str
    decision: Literal["BUY", "SKIP"]
    prediction_reliable: bool


@dataclass(frozen=True, slots=True)
class ResultArtifact:
    result_id: str
    race_id: str
    payload: Mapping[str, object]


class BacktestInputProvider(Protocol):
    def training_examples(self, years: tuple[int, ...]) -> tuple[TrainingExample, ...]: ...

    def races(self, test_year: int) -> tuple[BacktestRace, ...]: ...


class BacktestPredictor(Protocol):
    def predict(self, race: BacktestRace) -> PredictionSnapshot: ...


class BacktestTrainer(Protocol):
    def fit(
        self,
        manifest: TrainingManifest,
        examples: tuple[TrainingExample, ...],
    ) -> BacktestPredictor: ...


class RecommendationService(Protocol):
    def create(self, prediction: PredictionSnapshot) -> RecommendationArtifact: ...


class BacktestArtifactStore(Protocol):
    def persist_run_manifest(self, spec: BacktestSpec) -> None: ...

    def persist_fold_manifest(self, fold_id: str, training_years: tuple[int, ...]) -> None: ...

    def persist_artifact(
        self,
        artifact_id: str,
        artifact_kind: str,
        artifact_ref_id: str,
    ) -> None: ...

    def persist_prediction(self, prediction: PredictionSnapshot) -> None: ...

    def persist_recommendation(self, recommendation: RecommendationArtifact) -> None: ...

    def persisted_recommendation_ids(self, race_id: str) -> tuple[str, ...]: ...

    def record_guard_result(self, result: GuardResult) -> None: ...


class ResultReader(Protocol):
    def reveal(self, race_id: str, capability: object) -> ResultArtifact: ...


class MetricService(Protocol):
    def prediction_metrics(self, results: tuple[ResultArtifact, ...]) -> Mapping[str, object]: ...

    def betting_metrics(
        self,
        results: tuple[ResultArtifact, ...],
        odds_coverages: tuple[float, ...],
    ) -> Mapping[str, object] | None: ...


@dataclass(frozen=True, slots=True)
class BacktestServices:
    input_provider: BacktestInputProvider
    trainer: BacktestTrainer
    recommendation_service: RecommendationService
    artifact_store: BacktestArtifactStore
    result_reader: ResultReader
    metrics: MetricService


class BacktestOrchestrator:
    def run(self, spec: BacktestSpec, services: BacktestServices) -> BacktestRunResult:
        guard_result_ids: list[str] = []
        fold_ids: list[str] = []
        artifact_ids: list[str] = []
        results: list[ResultArtifact] = []
        odds_coverages: list[float] = []

        try:
            services.artifact_store.persist_run_manifest(spec)
            for fold in spec.folds:
                fold_ids.append(fold.fold_id)
                examples = services.input_provider.training_examples(fold.training_years)
                try:
                    training_manifest = TrainingManifest.create(
                        manifest_id=f"training-{spec.run_id}-{fold.fold_id}",
                        test_year=fold.test_year,
                        training_years=fold.training_years,
                        examples=examples,
                        feature_version_id=spec.feature_version_id,
                        model_version_id=spec.model_version_id,
                        logic_version_id=spec.logic_version_id,
                    )
                except ValueError as error:
                    self._check_and_record(
                        services,
                        guard_result_ids,
                        GuardResult.failed(
                            guard_result_id=f"guard-training-{fold.fold_id}",
                            guard_id="LEAK-002",
                            guard_version="LEAK-002-v1",
                            checked_input_ids=(example.example_id for example in examples),
                            details={"error": str(error)},
                        ),
                    )
                    raise
                services.artifact_store.persist_fold_manifest(
                    fold.fold_id,
                    training_manifest.training_years,
                )
                self._check_and_record(
                    services,
                    guard_result_ids,
                    BacktestGuards.check_training_window(training_manifest, fold),
                )
                predictor = services.trainer.fit(training_manifest, examples)
                races = sorted(
                    services.input_provider.races(fold.test_year),
                    key=lambda item: (item.as_of_time.value, item.race_id),
                )
                for race in races:
                    if race.test_year != fold.test_year:
                        self._check_and_record(
                            services,
                            guard_result_ids,
                            GuardResult.failed(
                                guard_result_id=f"guard-fold-year-{race.race_id}",
                                guard_id="LEAK-002",
                                guard_version="LEAK-002-v1",
                                checked_input_ids=(race.race_id,),
                                details={"expected": fold.test_year, "actual": race.test_year},
                            ),
                        )
                    self._check_and_record(
                        services,
                        guard_result_ids,
                        BacktestGuards.check_temporal_eligibility(
                            race.observations,
                            race.as_of_time,
                        ),
                    )
                    self._check_and_record(
                        services,
                        guard_result_ids,
                        BacktestGuards.check_ability_inputs(
                            (*race.observations, *race.feature_vectors),
                        ),
                    )
                    prediction = predictor.predict(race)
                    self._check_and_record(
                        services,
                        guard_result_ids,
                        BacktestGuards.check_versions(
                            required_versions={
                                "feature": spec.feature_version_id,
                                "model": spec.model_version_id,
                                "logic": spec.logic_version_id,
                            },
                            artifact_versions={
                                "feature": prediction.feature_version_id,
                                "model": prediction.model_version_id,
                                "logic": prediction.logic_version_id,
                            },
                        ),
                    )
                    services.artifact_store.persist_prediction(prediction)
                    artifact_ids.append(prediction.prediction_snapshot_id)
                    services.artifact_store.persist_artifact(
                        f"artifact-prediction-{prediction.prediction_snapshot_id}",
                        "prediction",
                        prediction.prediction_snapshot_id,
                    )
                    recommendation = services.recommendation_service.create(prediction)
                    services.artifact_store.persist_recommendation(recommendation)
                    services.artifact_store.persist_artifact(
                        f"artifact-recommendation-{recommendation.recommendation_id}",
                        "recommendation",
                        recommendation.recommendation_id,
                    )
                    recommendation_ids = services.artifact_store.persisted_recommendation_ids(
                        race.race_id,
                    )
                    capability = RecommendationPersistenceGate.issue(
                        race_id=race.race_id,
                        recommendation_ids=(recommendation.recommendation_id,),
                        persisted_ids=recommendation_ids,
                    )
                    result = services.result_reader.reveal(race.race_id, capability)
                    results.append(result)
                    services.artifact_store.persist_artifact(
                        f"artifact-result-{result.result_id}",
                        "result",
                        result.result_id,
                    )
                    odds_coverages.append(race.odds_coverage)

            prediction_metrics = services.metrics.prediction_metrics(tuple(results))
            betting_metrics = services.metrics.betting_metrics(
                tuple(results),
                tuple(odds_coverages),
            )
            return BacktestRunResult(
                run_id=spec.run_id,
                status=BacktestStatus.SUCCEEDED,
                fold_ids=tuple(fold_ids),
                guard_result_ids=tuple(guard_result_ids),
                artifact_ids=tuple(artifact_ids),
                official_metrics_available=True,
                diagnostic=None,
                prediction_metrics=dict(prediction_metrics),
                betting_metrics=dict(betting_metrics) if betting_metrics is not None else None,
            )
        except (GuardViolationError, ResultAccessDeniedError, ValueError) as error:
            return BacktestRunResult.invalid(
                run_id=spec.run_id,
                guard_result_ids=guard_result_ids,
                diagnostic=str(error),
            )

    @staticmethod
    def _check_and_record(
        services: BacktestServices,
        guard_result_ids: list[str],
        result: GuardResult,
    ) -> None:
        services.artifact_store.record_guard_result(result)
        guard_result_ids.append(result.guard_result_id)
        BacktestGuards.require_pass((result,))
