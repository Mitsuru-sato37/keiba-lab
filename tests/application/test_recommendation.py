from datetime import UTC, datetime
from decimal import Decimal

from keiba_lab.application.policy import RecommendationPolicy
from keiba_lab.application.recommendation import evaluate_win_recommendation


def prediction() -> dict[str, object]:
    return {
        "race_id": "R1",
        "horse_id": "H1",
        "win_probability": Decimal("0.25"),
        "uncertainty": Decimal("0.10"),
        "prediction_snapshot_id": "P1",
        "logic_version": "MODEL-WIN-001:v1",
        "calculated_at": datetime(2022, 1, 1, tzinfo=UTC),
    }


def test_win_evaluator_computes_exact_fair_odds_and_ev_and_buys_at_threshold() -> None:
    result = evaluate_win_recommendation(
        prediction(), Decimal("5.0"), RecommendationPolicy(min_ev=Decimal("1.25"))
    )
    assert result.decision == "BUY"
    assert result.fair_odds == Decimal("4")
    assert result.expected_value == Decimal("1.25")


def test_win_evaluator_returns_wait_without_odds() -> None:
    result = evaluate_win_recommendation(prediction(), None, RecommendationPolicy())
    assert result.decision == "WAIT"
    assert result.reason_codes == ("ODDS_UNAVAILABLE",)


def test_win_evaluator_returns_skip_for_low_value_or_unreliable_prediction() -> None:
    low = evaluate_win_recommendation(prediction(), Decimal("4.0"), RecommendationPolicy())
    assert low.decision == "SKIP" and low.reason_codes == ("SKIP_NO_VALUE",)
    unreliable = evaluate_win_recommendation(
        {**prediction(), "uncertainty": Decimal("0.50")}, Decimal("8.0"), RecommendationPolicy()
    )
    assert unreliable.decision == "SKIP" and unreliable.reason_codes == ("SKIP_UNRELIABLE",)
