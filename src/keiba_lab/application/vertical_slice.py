from datetime import date, datetime
from decimal import Decimal
from types import MappingProxyType
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, Field

from keiba_lab.application.policy import RecommendationPolicy
from keiba_lab.application.recommendation import WinRecommendation, evaluate_win_recommendation
from keiba_lab.persistence.repositories import AppendOnlyRepository
from keiba_lab.providers.ports import RaceProvider


class PredictionEvidence(BaseModel):
    model_config = ConfigDict(frozen=True)
    race_id: str
    horse_id: str
    win_probability: Decimal
    uncertainty: Decimal
    prediction_snapshot_id: str
    logic_version: str
    calculated_at: datetime


class RaceSummary(BaseModel):
    model_config = ConfigDict(frozen=True)
    race_id: str
    post_time: datetime
    runner_count: int = Field(ge=1)
    data_status: str = "READY"
    recommendation_state: str


class RaceDetail(BaseModel):
    model_config = ConfigDict(frozen=True)
    race_id: str
    post_time: datetime
    prediction: PredictionEvidence
    recommendation: WinRecommendation


class Phase1Service:
    def __init__(self, provider: RaceProvider, policy: RecommendationPolicy) -> None:
        self.provider = provider
        self.policy = policy
        self._predictions: dict[str, PredictionEvidence] = {}
        self._recommendations: dict[str, list[WinRecommendation]] = {}
        self._odds: dict[str, Decimal] = {}
        self.race_snapshots = AppendOnlyRepository()
        self.prediction_snapshots = AppendOnlyRepository()
        self.odds_snapshots = AppendOnlyRepository()
        self.recommendation_artifacts = AppendOnlyRepository()

    def list_today(self, race_date: date, as_of_time: datetime) -> tuple[RaceSummary, ...]:
        requested_date = race_date.date() if isinstance(race_date, datetime) else race_date
        return tuple(
            RaceSummary(
                race_id=race.race_id,
                post_time=race.scheduled_post_time,
                runner_count=len(race.runners),
                recommendation_state=self.get_race(
                    race.race_id, as_of_time
                ).recommendation.decision,
            )
            for race in self.provider.list_races(as_of_time)
            if race.scheduled_post_time.astimezone(ZoneInfo("Asia/Tokyo")).date() == requested_date
        )

    def get_race(self, race_id: str, as_of_time: datetime) -> RaceDetail:
        race = self.provider.get_race(race_id, as_of_time)
        if race is None:
            raise KeyError(race_id)
        prediction = self._predictions.setdefault(
            race_id,
            PredictionEvidence(
                race_id=race_id,
                horse_id=race.runners[0].horse_id,
                win_probability=Decimal("0.25"),
                uncertainty=Decimal("0.10"),
                prediction_snapshot_id=f"PRED-{race_id}-1",
                logic_version="MODEL-WIN-001:v1",
                calculated_at=as_of_time,
            ),
        )
        if prediction.prediction_snapshot_id not in {
            item["prediction_snapshot_id"] for item in self.prediction_snapshots.all()
        }:
            self.race_snapshots.append(
                f"SNAPSHOT-{race_id}",
                {
                    "race_id": race_id,
                    "as_of_time": as_of_time.isoformat(),
                    "logic_version": "SNAP-001:v1",
                },
            )
            self.prediction_snapshots.append(
                prediction.prediction_snapshot_id, prediction.model_dump(mode="json")
            )
        latest = self._recommendations.get(race_id, [])
        recommendation = (
            latest[-1]
            if latest
            else evaluate_win_recommendation(
                MappingProxyType(prediction.model_dump()), None, self.policy
            )
        )
        return RaceDetail(
            race_id=race_id,
            post_time=race.scheduled_post_time,
            prediction=prediction,
            recommendation=recommendation,
        )

    def update_odds(
        self, race_id: str, odds_input: Decimal, calculated_at: datetime
    ) -> WinRecommendation:
        detail = self.get_race(race_id, calculated_at)
        self._odds[race_id] = odds_input
        result = evaluate_win_recommendation(
            MappingProxyType(detail.prediction.model_dump()), odds_input, self.policy
        )
        odds_id = f"ODDS-{race_id}-{len(self.odds_snapshots.all()) + 1}"
        self.odds_snapshots.append(
            odds_id,
            {
                "odds_snapshot_id": odds_id,
                "race_id": race_id,
                "current_odds": str(odds_input),
                "prediction_snapshot_id": detail.prediction.prediction_snapshot_id,
            },
        )
        self._recommendations.setdefault(race_id, []).append(result)
        recommendation_id = f"RECO-{race_id}-{len(self.recommendation_artifacts.all()) + 1}"
        self.recommendation_artifacts.append(
            recommendation_id,
            {
                "recommendation_id": recommendation_id,
                **result.model_dump(mode="json"),
                "odds_snapshot_id": odds_id,
            },
        )
        return result

    def recommendations(self, race_id: str) -> tuple[WinRecommendation, ...]:
        initial = self.get_race(
            race_id, datetime(2022, 1, 1, tzinfo=__import__("datetime").UTC)
        ).recommendation
        return (initial, *self._recommendations.get(race_id, ()))
