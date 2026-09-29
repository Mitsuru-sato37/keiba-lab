from datetime import datetime, timedelta
from decimal import Decimal
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from keiba_lab.domain.enums import BetType, Decision, SkipCategory, Strategy


class DomainModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


Probability = Annotated[Decimal, Field(ge=0, le=1)]


def require_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("datetime must be timezone-aware")
    if value.utcoffset() != timedelta(0):
        raise ValueError("datetime must be UTC")
    return value


class RunnerSnapshot(DomainModel):
    horse_id: str = Field(min_length=1)
    horse_number: int = Field(ge=1)


class RaceSnapshot(DomainModel):
    race_id: str = Field(min_length=1)
    snapshot_id: str = Field(min_length=1)
    as_of_time: datetime
    scheduled_post_time: datetime
    runners: tuple[RunnerSnapshot, ...] = Field(min_length=1)

    @field_validator("as_of_time", "scheduled_post_time")
    @classmethod
    def require_utc_datetime(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("datetime must be timezone-aware")
        if value.utcoffset() != timedelta(0):
            raise ValueError("datetime must be UTC")
        return value


class VersionRef(DomainModel):
    name: str = Field(min_length=1)
    version: str = Field(min_length=1)


class HorsePrediction(DomainModel):
    horse_id: str = Field(min_length=1)
    win_probability: Probability
    top2_probability: Probability
    top3_probability: Probability
    ranking_score: Decimal
    uncertainty: Probability
    model_version: VersionRef
    feature_version: VersionRef
    calibration_version: VersionRef
    logic_version: VersionRef
    input_snapshot_id: str = Field(min_length=1)
    calculated_at: datetime

    @model_validator(mode="after")
    def validate_probability_order(self) -> Self:
        if not self.win_probability <= self.top2_probability <= self.top3_probability:
            raise ValueError("probabilities must satisfy win <= top2 <= top3")
        return self

    @field_validator("calculated_at")
    @classmethod
    def require_utc_calculated_at(cls, value: datetime) -> datetime:
        return require_utc(value)


class BetCandidate(DomainModel):
    bet_type: BetType
    combination: tuple[str, ...] = Field(min_length=1)
    model_probability: Probability
    current_odds: Decimal = Field(gt=0)
    predicted_final_odds: Decimal = Field(gt=0)
    conservative_probability: Probability
    conservative_odds: Decimal = Field(gt=0)
    expected_value: Decimal
    uncertainty: Probability
    prediction_snapshot_id: str = Field(min_length=1)
    simulation_result_id: str = Field(min_length=1)
    odds_snapshot_id: str = Field(min_length=1)
    overlap_group: str = Field(min_length=1)
    model_version: VersionRef
    feature_version: VersionRef
    calibration_version: VersionRef
    logic_version: VersionRef
    calculated_at: datetime

    @field_validator("calculated_at")
    @classmethod
    def require_utc_calculated_at(cls, value: datetime) -> datetime:
        return require_utc(value)

    @model_validator(mode="after")
    def validate_combination(self) -> Self:
        expected_size = {
            BetType.WIN: 1,
            BetType.PLACE: 1,
            BetType.QUINELLA: 2,
            BetType.EXACTA: 2,
            BetType.WIDE: 2,
            BetType.TRIO: 3,
            BetType.TRIFECTA: 3,
        }[self.bet_type]
        if len(self.combination) != expected_size or len(set(self.combination)) != expected_size:
            raise ValueError("combination has invalid size or duplicate horses")
        if self.bet_type in {
            BetType.QUINELLA,
            BetType.WIDE,
            BetType.TRIO,
        } and self.combination != tuple(sorted(self.combination)):
            raise ValueError("unordered bet combination must be sorted")
        return self


class RecommendationItem(DomainModel):
    candidate: BetCandidate
    amount_yen: int = Field(ge=100, multiple_of=100)


class Recommendation(DomainModel):
    recommendation_id: str = Field(min_length=1)
    prediction_snapshot_id: str = Field(min_length=1)
    strategy: Strategy
    decision: Decision
    items: tuple[RecommendationItem, ...]
    skip_category: SkipCategory | None = None
    reason_codes: tuple[str, ...]
    logic_version: VersionRef
    calculated_at: datetime

    @field_validator("calculated_at")
    @classmethod
    def require_utc_calculated_at(cls, value: datetime) -> datetime:
        return require_utc(value)

    @model_validator(mode="after")
    def validate_decision_state(self) -> Self:
        if self.decision is Decision.BUY:
            if not self.items:
                raise ValueError("BUY requires items")
            if self.skip_category is not None:
                raise ValueError("BUY cannot have a skip category")
        else:
            if self.items:
                raise ValueError("SKIP cannot contain items")
            if self.skip_category is None or not self.reason_codes:
                raise ValueError("SKIP requires a category and reason codes")
        return self
