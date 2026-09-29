from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError

from keiba_lab.domain.enums import BetType, Decision, SkipCategory, Strategy
from keiba_lab.domain.models import (
    BetCandidate,
    HorsePrediction,
    RaceSnapshot,
    Recommendation,
    RecommendationItem,
    RunnerSnapshot,
    VersionRef,
)


def test_stable_external_enum_values() -> None:
    assert Decision.BUY.value == "BUY"
    assert Decision.SKIP.value == "SKIP"
    assert Strategy.LONGSHOT.value == "LONGSHOT"


def test_race_snapshot_rejects_naive_as_of_time() -> None:
    runner = RunnerSnapshot(horse_id="H1", horse_number=1)
    with pytest.raises(ValidationError, match="timezone-aware"):
        RaceSnapshot(
            race_id="R1",
            snapshot_id="S1",
            as_of_time=datetime(2022, 1, 1),
            scheduled_post_time=datetime(2022, 1, 1, 6, tzinfo=UTC),
            runners=(runner,),
        )


def test_race_snapshot_rejects_non_utc_time() -> None:
    runner = RunnerSnapshot(horse_id="H1", horse_number=1)
    with pytest.raises(ValidationError, match="must be UTC"):
        RaceSnapshot(
            race_id="R1",
            snapshot_id="S1",
            as_of_time=datetime(2022, 1, 1, 9, tzinfo=timezone(timedelta(hours=9))),
            scheduled_post_time=datetime(2022, 1, 1, 6, tzinfo=UTC),
            runners=(runner,),
        )


def valid_prediction_payload() -> dict[str, object]:
    version = VersionRef(name="core", version="1")
    return {
        "horse_id": "H1",
        "win_probability": Decimal("0.20"),
        "top2_probability": Decimal("0.40"),
        "top3_probability": Decimal("0.60"),
        "ranking_score": Decimal("1.2"),
        "uncertainty": Decimal("0.10"),
        "model_version": version,
        "feature_version": version,
        "calibration_version": version,
        "logic_version": version,
        "input_snapshot_id": "S1",
        "calculated_at": datetime(2022, 1, 1, tzinfo=UTC),
    }


def test_prediction_requires_monotonic_finish_probabilities() -> None:
    payload = valid_prediction_payload()
    payload["top2_probability"] = Decimal("0.10")
    with pytest.raises(ValidationError, match="win <= top2 <= top3"):
        HorsePrediction(**payload)


@pytest.mark.parametrize(
    "field,value", [("win_probability", "-0.01"), ("top3_probability", "1.01")]
)
def test_prediction_rejects_probability_outside_unit_interval(field: str, value: str) -> None:
    payload = valid_prediction_payload()
    payload[field] = Decimal(value)
    with pytest.raises(ValidationError):
        HorsePrediction(**payload)


def test_prediction_rejects_non_utc_calculated_at() -> None:
    payload = valid_prediction_payload()
    payload["calculated_at"] = datetime(2022, 1, 1, 9, tzinfo=timezone(timedelta(hours=9)))
    with pytest.raises(ValidationError, match="must be UTC"):
        HorsePrediction(**payload)


def test_version_ref_rejects_blank_values() -> None:
    with pytest.raises(ValidationError):
        VersionRef(name="", version="1")


def test_domain_models_are_frozen_and_reject_extra_fields() -> None:
    version = VersionRef(name="core", version="1")
    with pytest.raises(ValidationError):
        version.version = "2"
    with pytest.raises(ValidationError):
        VersionRef(name="core", version="1", unknown="x")


def valid_candidate_payload() -> dict[str, object]:
    version = VersionRef(name="core", version="1")
    return {
        "bet_type": BetType.WIN,
        "combination": ("H1",),
        "model_probability": Decimal("0.30"),
        "current_odds": Decimal("4.0"),
        "predicted_final_odds": Decimal("3.8"),
        "conservative_probability": Decimal("0.25"),
        "conservative_odds": Decimal("3.5"),
        "expected_value": Decimal("0.875"),
        "uncertainty": Decimal("0.10"),
        "prediction_snapshot_id": "P1",
        "simulation_result_id": "SIM1",
        "odds_snapshot_id": "O1",
        "overlap_group": "R1:H1",
        "model_version": version,
        "feature_version": version,
        "calibration_version": version,
        "logic_version": version,
        "calculated_at": datetime(2022, 1, 1, tzinfo=UTC),
    }


def make_item() -> RecommendationItem:
    return RecommendationItem(candidate=BetCandidate(**valid_candidate_payload()), amount_yen=100)


def test_candidate_rejects_noncanonical_combination() -> None:
    payload = valid_candidate_payload()
    payload.update(bet_type=BetType.QUINELLA, combination=("H2", "H1"))
    with pytest.raises(ValidationError):
        BetCandidate(**payload)


def test_candidate_requires_positive_odds() -> None:
    payload = valid_candidate_payload()
    payload["current_odds"] = Decimal("0")
    with pytest.raises(ValidationError):
        BetCandidate(**payload)


def test_buy_requires_items_and_no_skip_category() -> None:
    with pytest.raises(ValidationError, match="BUY requires items"):
        Recommendation(
            recommendation_id="R",
            prediction_snapshot_id="P",
            strategy=Strategy.STABLE,
            decision=Decision.BUY,
            items=(),
            reason_codes=(),
            logic_version=VersionRef(name="r", version="1"),
            calculated_at=datetime(2022, 1, 1, tzinfo=UTC),
        )
    with pytest.raises(ValidationError, match="BUY cannot"):
        Recommendation(
            recommendation_id="R",
            prediction_snapshot_id="P",
            strategy=Strategy.STABLE,
            decision=Decision.BUY,
            items=(make_item(),),
            skip_category=SkipCategory.NO_VALUE,
            reason_codes=("x",),
            logic_version=VersionRef(name="r", version="1"),
            calculated_at=datetime(2022, 1, 1, tzinfo=UTC),
        )


def test_skip_rejects_purchase_items() -> None:
    with pytest.raises(ValidationError, match="SKIP cannot"):
        Recommendation(
            recommendation_id="R",
            prediction_snapshot_id="P",
            strategy=Strategy.STABLE,
            decision=Decision.SKIP,
            items=(make_item(),),
            skip_category=SkipCategory.NO_VALUE,
            reason_codes=("x",),
            logic_version=VersionRef(name="r", version="1"),
            calculated_at=datetime(2022, 1, 1, tzinfo=UTC),
        )
