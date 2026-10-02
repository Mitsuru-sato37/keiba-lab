from datetime import UTC, datetime, timedelta
from typing import Any

from keiba_application.backtest import BacktestRunResult, BacktestSpec, BacktestStatus
from keiba_application.backtest_engine import (
    BacktestArtifactStore,
    BacktestInputProvider,
    BacktestOrchestrator,
    BacktestRace,
    BacktestServices,
    RecommendationArtifact,
    ResultArtifact,
)
from keiba_application.errors import ResultAccessDeniedError
from keiba_application.ports import ObservationRecord
from keiba_application.predictions import (
    PredictionSnapshot,
    RunnerPrediction,
    TrainingExample,
)
from keiba_application.snapshots import FeatureVector
from keiba_domain.time_values import UtcInstant

BASE_TIME = datetime(2022, 1, 1, 3, tzinfo=UTC)
BASE_INSTANT = UtcInstant.from_datetime(BASE_TIME)


def make_spec(*, test_years: tuple[int, ...] = (2022, 2023)) -> BacktestSpec:
    return BacktestSpec.create(
        run_id="run-engine-1",
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


def example(example_id: str, year: int) -> TrainingExample:
    return TrainingExample(
        example_id=example_id,
        race_id=f"training-race-{example_id}",
        runner_id=f"training-runner-{example_id}",
        race_year=year,
        feature_version_id="core-feature-v1",
        features={"runner.gate": 1},
        won=year % 2 == 0,
        top2=True,
        top3=True,
    )


def feature_vector(race_id: str, runner_id: str, as_of_time: UtcInstant) -> FeatureVector:
    return FeatureVector(
        feature_snapshot_id=f"feature-{race_id}-{runner_id}",
        race_id=race_id,
        runner_id=runner_id,
        as_of_time=as_of_time,
        data_snapshot_id=f"snapshot-{race_id}",
        feature_version_id="core-feature-v1",
        logic_version_id="FEAT-001-v1",
        values={"runner.gate": 1},
        source_observation_ids=(f"observation-{race_id}",),
        missing_fields=(),
    )


def race(
    race_id: str,
    year: int,
    *,
    offset_minutes: int,
    received_time: UtcInstant = BASE_INSTANT,
    payload: dict[str, object] | None = None,
    odds_coverage: float = 1.0,
) -> BacktestRace:
    as_of_time = UtcInstant.from_datetime(BASE_TIME + timedelta(minutes=offset_minutes))
    observation = ObservationRecord(
        record_id=f"observation-{race_id}",
        source="fixture",
        source_version="fixture-v1",
        source_timestamp=BASE_INSTANT,
        received_timestamp=received_time,
        effective_from=BASE_INSTANT,
        payload=payload or {"race_id": race_id, "runner_id": "runner-1"},
        provider_record_type="runner",
    )
    return BacktestRace(
        race_id=race_id,
        test_year=year,
        as_of_time=as_of_time,
        feature_vectors=(feature_vector(race_id, "runner-1", as_of_time),),
        observations=(observation,),
        result_payload={"winner": "runner-1"},
        odds_coverage=odds_coverage,
    )


class FixtureInputProvider(BacktestInputProvider):
    def __init__(self, races_by_year: dict[int, tuple[BacktestRace, ...]]) -> None:
        self.races_by_year = races_by_year
        self.training_requests: list[tuple[int, ...]] = []
        self.race_requests: list[int] = []

    def training_examples(self, years: tuple[int, ...]) -> tuple[TrainingExample, ...]:
        self.training_requests.append(years)
        return tuple(example(f"example-{year}", year) for year in years)

    def races(self, test_year: int) -> tuple[BacktestRace, ...]:
        self.race_requests.append(test_year)
        return self.races_by_year[test_year]


class ContaminatedInputProvider(FixtureInputProvider):
    def training_examples(self, years: tuple[int, ...]) -> tuple[TrainingExample, ...]:
        return (*super().training_examples(years), example("contaminated", 2022))


class FixturePredictor:
    def __init__(self, events: list[str]) -> None:
        self.events = events
        self.predicted_races: list[str] = []

    def predict(self, race_input: BacktestRace) -> PredictionSnapshot:
        self.events.append(f"predict:{race_input.race_id}")
        self.predicted_races.append(race_input.race_id)
        return PredictionSnapshot(
            prediction_snapshot_id=f"prediction-{race_input.race_id}",
            race_id=race_input.race_id,
            as_of_time=race_input.as_of_time,
            data_snapshot_id=f"snapshot-{race_input.race_id}",
            feature_version_id="core-feature-v1",
            model_version_id="baseline-gate-v1",
            logic_version_id="MODEL-BASE-001-v1",
            training_manifest_id="training-manifest",
            model_manifest_checksum="m" * 64,
            calibration_version_id=None,
            predictions=(
                RunnerPrediction(
                    runner_id="runner-1",
                    raw_win_probability=1.0,
                    win_probability=1.0,
                    raw_top2_probability=1.0,
                    top2_probability=1.0,
                    raw_top3_probability=1.0,
                    top3_probability=1.0,
                    ranking_score=1.0,
                    uncertainty=0.0,
                    disagreement=0.0,
                ),
            ),
        )


class FixtureTrainer:
    def __init__(self, events: list[str]) -> None:
        self.events = events
        self.training_years: list[tuple[int, ...]] = []
        self.predictors: list[FixturePredictor] = []

    def fit(self, manifest: Any, examples: tuple[TrainingExample, ...]) -> FixturePredictor:
        self.events.append(f"train:{manifest.test_year}")
        self.training_years.append(tuple(sorted({example.race_year for example in examples})))
        predictor = FixturePredictor(self.events)
        self.predictors.append(predictor)
        return predictor


class FixtureRecommendationService:
    def __init__(self, events: list[str]) -> None:
        self.events = events

    def create(self, prediction: PredictionSnapshot) -> RecommendationArtifact:
        self.events.append(f"recommend:{prediction.race_id}")
        return RecommendationArtifact(
            recommendation_id=f"recommendation-{prediction.race_id}",
            race_id=prediction.race_id,
            prediction_snapshot_id=prediction.prediction_snapshot_id,
            decision="SKIP",
            prediction_reliable=True,
        )


class FixtureStore(BacktestArtifactStore):
    def __init__(self, events: list[str], *, persist: bool = True) -> None:
        self.events = events
        self.persist = persist
        self.predictions: dict[str, PredictionSnapshot] = {}
        self.recommendations: dict[str, RecommendationArtifact] = {}
        self.run_manifests: list[BacktestSpec] = []
        self.fold_manifests: list[tuple[str, tuple[int, ...]]] = []
        self.artifacts: list[tuple[str, str, str]] = []

    def persist_run_manifest(self, spec: BacktestSpec) -> None:
        self.events.append("persist-run-manifest")
        self.run_manifests.append(spec)

    def persist_fold_manifest(self, fold_id: str, training_years: tuple[int, ...]) -> None:
        self.events.append(f"persist-fold-manifest:{fold_id}")
        self.fold_manifests.append((fold_id, training_years))

    def persist_artifact(self, artifact_id: str, artifact_kind: str, artifact_ref_id: str) -> None:
        self.events.append(f"persist-artifact:{artifact_kind}:{artifact_ref_id}")
        self.artifacts.append((artifact_id, artifact_kind, artifact_ref_id))

    def persist_prediction(self, prediction: PredictionSnapshot) -> None:
        self.events.append(f"persist-prediction:{prediction.race_id}")
        self.predictions[prediction.race_id] = prediction

    def persist_recommendation(self, recommendation: RecommendationArtifact) -> None:
        self.events.append(f"persist-recommendation:{recommendation.race_id}")
        if self.persist:
            self.recommendations[recommendation.recommendation_id] = recommendation

    def persisted_recommendation_ids(self, race_id: str) -> tuple[str, ...]:
        return tuple(
            recommendation_id
            for recommendation_id, recommendation in self.recommendations.items()
            if recommendation.race_id == race_id
        )

    def record_guard_result(self, result: Any) -> None:
        self.events.append(f"guard:{result.guard_id}:{result.status.value}")


class FixtureResultReader:
    def __init__(self, events: list[str]) -> None:
        self.events = events

    def reveal(self, race_id: str, capability: Any) -> ResultArtifact:
        if not capability.allows(race_id):
            raise ResultAccessDeniedError(race_id)
        self.events.append(f"result:{race_id}")
        return ResultArtifact(
            result_id=f"result-{race_id}",
            race_id=race_id,
            payload={"winner": "runner-1"},
        )


class FixtureMetrics:
    def prediction_metrics(self, results: tuple[ResultArtifact, ...]) -> dict[str, object]:
        return {"result_count": len(results)}

    def betting_metrics(
        self,
        results: tuple[ResultArtifact, ...],
        odds_coverages: tuple[float, ...],
    ) -> dict[str, object] | None:
        if not odds_coverages or min(odds_coverages) < 1.0:
            return None
        return {"result_count": len(results), "roi": 0.0}


def services(
    provider: FixtureInputProvider,
    events: list[str],
    *,
    persist: bool = True,
) -> BacktestServices:
    return BacktestServices(
        input_provider=provider,
        trainer=FixtureTrainer(events),
        recommendation_service=FixtureRecommendationService(events),
        artifact_store=FixtureStore(events, persist=persist),
        result_reader=FixtureResultReader(events),
        metrics=FixtureMetrics(),
    )


def test_orchestrator_processes_races_in_order_and_expands_training_window() -> None:
    events: list[str] = []
    provider = FixtureInputProvider(
        {
            2022: (
                race("race-2022-b", 2022, offset_minutes=2),
                race("race-2022-a", 2022, offset_minutes=1),
            ),
            2023: (race("race-2023-a", 2023, offset_minutes=1),),
        },
    )
    execution_services = services(provider, events)

    result = BacktestOrchestrator().run(make_spec(), execution_services)

    assert result.status is BacktestStatus.SUCCEEDED
    assert isinstance(execution_services.artifact_store, FixtureStore)
    store = execution_services.artifact_store
    assert store.run_manifests == [make_spec()]
    assert store.fold_manifests == [
        ("fold-2022", (2019, 2020, 2021)),
        ("fold-2023", (2019, 2020, 2021, 2022)),
    ]
    assert store.artifacts
    assert provider.training_requests == [(2019, 2020, 2021), (2019, 2020, 2021, 2022)]
    assert events.index("predict:race-2022-a") < events.index("persist-recommendation:race-2022-a")
    assert events.index("persist-recommendation:race-2022-a") < events.index("result:race-2022-a")
    assert events.index("result:race-2022-a") < events.index("train:2023")
    assert "predict:race-2022-b" in events


def test_orchestrator_reports_prediction_metrics_without_betting_metrics_for_incomplete_odds(
) -> None:
    events: list[str] = []
    provider = FixtureInputProvider(
        {2022: (race("race-1", 2022, offset_minutes=1, odds_coverage=0.5),)},
    )

    result = BacktestOrchestrator().run(
        make_spec(test_years=(2022,)),
        services(provider, events),
    )

    assert result.status is BacktestStatus.SUCCEEDED
    assert result.prediction_metrics == {"result_count": 1}
    assert result.betting_metrics is None


def test_failed_temporal_guard_invalidates_run_and_stops_later_folds() -> None:
    events: list[str] = []
    future = UtcInstant.from_datetime(BASE_TIME + timedelta(hours=1))
    provider = FixtureInputProvider(
        {
            2022: (race("race-leak", 2022, offset_minutes=1, received_time=future),),
            2023: (race("race-should-not-run", 2023, offset_minutes=1),),
        },
    )

    result = BacktestOrchestrator().run(make_spec(), services(provider, events))

    assert isinstance(result, BacktestRunResult)
    assert result.status is BacktestStatus.INVALID
    assert result.official_metrics_available is False
    assert provider.race_requests == [2022]
    assert not any(event.startswith("predict:") for event in events)


def test_training_contamination_records_leak_guard_before_invalidating_run() -> None:
    events: list[str] = []
    provider = ContaminatedInputProvider({2022: (race("race-1", 2022, offset_minutes=1),)})

    result = BacktestOrchestrator().run(
        make_spec(test_years=(2022,)),
        services(provider, events),
    )

    assert result.status is BacktestStatus.INVALID
    assert result.guard_result_ids
    assert "guard:LEAK-002:fail" in events


def test_current_race_odds_never_reach_prediction() -> None:
    events: list[str] = []
    provider = FixtureInputProvider(
        {
            2022: (
                race(
                    "race-odds",
                    2022,
                    offset_minutes=1,
                    payload={"race_id": "race-odds", "runner_id": "runner-1", "odds": {"win": 2.5}},
                ),
            ),
        },
    )

    result = BacktestOrchestrator().run(
        make_spec(test_years=(2022,)),
        services(provider, events),
    )

    assert result.status is BacktestStatus.INVALID
    assert not any(event.startswith("predict:") for event in events)


def test_partial_recommendation_persistence_invalidates_run_before_result_reveal() -> None:
    events: list[str] = []
    provider = FixtureInputProvider(
        {2022: (race("race-no-recommendation", 2022, offset_minutes=1),)},
    )

    result = BacktestOrchestrator().run(
        make_spec(test_years=(2022,)),
        services(provider, events, persist=False),
    )

    assert result.status is BacktestStatus.INVALID
    assert not any(event.startswith("result:") for event in events)
