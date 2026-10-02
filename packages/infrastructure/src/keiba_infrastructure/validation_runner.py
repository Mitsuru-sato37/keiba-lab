from collections.abc import Mapping
from dataclasses import dataclass

from keiba_application.backtest import BacktestRunResult, BacktestSpec, GuardResult
from keiba_application.backtest_engine import (
    BacktestArtifactStore,
    BacktestInputProvider,
    BacktestOrchestrator,
    BacktestPredictor,
    BacktestRace,
    BacktestServices,
    BacktestTrainer,
    RecommendationArtifact,
    RecommendationService,
    ResultArtifact,
    ResultReader,
)
from keiba_application.errors import ResultAccessDeniedError
from keiba_application.predictions import PredictionSnapshot, TrainingExample, TrainingManifest

from keiba_infrastructure.baseline_prediction import (
    BASELINE_LOGIC_VERSION_ID,
    BASELINE_MODEL_VERSION_ID,
    GateStrengthBaseline,
    TrainedGateStrengthBaseline,
)

from .validation_fixture import (
    ExpectedRecommendation,
    OneDayValidationFixture,
    OneDayValidationInputProvider,
    RecommendationDecision,
)


@dataclass(frozen=True, slots=True)
class OneDayValidationReport:
    fixture_checksum: str
    ordered_race_ids: tuple[str, ...]
    recommendation_decisions: Mapping[str, RecommendationDecision]
    events: tuple[str, ...]
    result: BacktestRunResult


class _BaselinePredictor(BacktestPredictor):
    def __init__(self, model: TrainedGateStrengthBaseline, events: list[str]) -> None:
        self._model = model
        self._events = events

    def predict(self, race: BacktestRace) -> PredictionSnapshot:
        self._events.append(f"predict:{race.race_id}")
        return self._model.predict(race.feature_vectors)


class _BaselineTrainer(BacktestTrainer):
    def __init__(self, events: list[str]) -> None:
        self._events = events

    def fit(
        self,
        manifest: TrainingManifest,
        examples: tuple[TrainingExample, ...],
    ) -> BacktestPredictor:
        self._events.append(f"train:{manifest.test_year}")
        model = GateStrengthBaseline.fit(manifest=manifest, examples=examples)
        return _BaselinePredictor(model, self._events)


class _FixtureRecommendationService(RecommendationService):
    def __init__(
        self,
        expected: Mapping[str, ExpectedRecommendation],
        events: list[str],
    ) -> None:
        self._expected = expected
        self._events = events
        self.decisions: dict[str, RecommendationDecision] = {}

    def create(self, prediction: PredictionSnapshot) -> RecommendationArtifact:
        expected = self._expected[prediction.race_id]
        self.decisions[prediction.race_id] = expected.decision
        self._events.append(f"recommend:{prediction.race_id}")
        return RecommendationArtifact(
            recommendation_id=f"recommendation-{prediction.race_id}",
            race_id=prediction.race_id,
            prediction_snapshot_id=prediction.prediction_snapshot_id,
            decision=expected.decision,
            prediction_reliable=True,
        )


class _InMemoryArtifactStore(BacktestArtifactStore):
    def __init__(self, events: list[str]) -> None:
        self._events = events
        self._recommendations: dict[str, RecommendationArtifact] = {}

    def persist_run_manifest(self, spec: BacktestSpec) -> None:
        self._events.append("persist-run-manifest")

    def persist_fold_manifest(self, fold_id: str, training_years: tuple[int, ...]) -> None:
        self._events.append(f"persist-fold-manifest:{fold_id}:{training_years}")

    def persist_artifact(self, artifact_id: str, artifact_kind: str, artifact_ref_id: str) -> None:
        self._events.append(f"persist-artifact:{artifact_kind}:{artifact_ref_id}")

    def persist_prediction(self, prediction: PredictionSnapshot) -> None:
        self._events.append(f"persist-prediction:{prediction.race_id}")

    def persist_recommendation(self, recommendation: RecommendationArtifact) -> None:
        self._recommendations[recommendation.recommendation_id] = recommendation
        self._events.append(f"persist-recommendation:{recommendation.race_id}")

    def persisted_recommendation_ids(self, race_id: str) -> tuple[str, ...]:
        return tuple(
            recommendation_id
            for recommendation_id, recommendation in self._recommendations.items()
            if recommendation.race_id == race_id
        )

    def record_guard_result(self, result: GuardResult) -> None:
        self._events.append(f"guard:{result.guard_id}:{result.status.value}")


class _FixtureResultReader(ResultReader):
    def __init__(self, races: tuple[BacktestRace, ...], events: list[str]) -> None:
        self._payloads = {race.race_id: race.result_payload for race in races}
        self._events = events

    def reveal(self, race_id: str, capability: object) -> ResultArtifact:
        allows = getattr(capability, "allows", None)
        if not callable(allows) or not allows(race_id):
            raise ResultAccessDeniedError(race_id)
        self._events.append(f"result:{race_id}")
        return ResultArtifact(
            result_id=f"result-{race_id}",
            race_id=race_id,
            payload=self._payloads[race_id],
        )


class _CoverageMetrics:
    def prediction_metrics(self, results: tuple[ResultArtifact, ...]) -> Mapping[str, object]:
        return {"result_count": len(results)}

    def betting_metrics(
        self,
        results: tuple[ResultArtifact, ...],
        odds_coverages: tuple[float, ...],
    ) -> Mapping[str, object] | None:
        if not odds_coverages or min(odds_coverages) < 1.0:
            return None
        return {"result_count": len(results), "roi": 0.0}


def _validation_spec(fixture: OneDayValidationFixture) -> BacktestSpec:
    return BacktestSpec.create(
        run_id=f"validation-{fixture.target_date.isoformat()}",
        test_years=(2022,),
        feature_version_id="core-feature-v1",
        model_version_id=BASELINE_MODEL_VERSION_ID,
        logic_version_id=BASELINE_LOGIC_VERSION_ID,
        calibration_version_id=None,
        config_checksum=fixture.checksum,
        code_revision="2022-one-day-validation-v1",
        dependency_lock_checksum="keiba-lab-lock-v1",
        random_seeds={"validation": fixture.seed},
    )


def run_one_day_validation(fixture: OneDayValidationFixture) -> OneDayValidationReport:
    events: list[str] = []
    provider: BacktestInputProvider = OneDayValidationInputProvider(fixture)
    recommendation_service = _FixtureRecommendationService(
        fixture.expected_recommendations,
        events,
    )
    services = BacktestServices(
        input_provider=provider,
        trainer=_BaselineTrainer(events),
        recommendation_service=recommendation_service,
        artifact_store=_InMemoryArtifactStore(events),
        result_reader=_FixtureResultReader(fixture.races, events),
        metrics=_CoverageMetrics(),
    )
    result = BacktestOrchestrator().run(_validation_spec(fixture), services)
    return OneDayValidationReport(
        fixture_checksum=fixture.checksum,
        ordered_race_ids=tuple(race.race_id for race in fixture.races),
        recommendation_decisions=dict(recommendation_service.decisions),
        events=tuple(events),
        result=result,
    )
