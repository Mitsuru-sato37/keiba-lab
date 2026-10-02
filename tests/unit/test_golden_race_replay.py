from keiba_application.golden_replay import (
    CoverageAwareEvaluator,
    PersistedPrediction,
    PolicyReplay,
)


def prediction() -> PersistedPrediction:
    return PersistedPrediction(
        prediction_snapshot_id="prediction-1",
        race_id="race-1",
        probabilities={"horse-1": 0.6, "horse-2": 0.4},
        model_version_id="model-1",
    )


def test_policy_replay_does_not_change_prediction_or_retrain() -> None:
    original = prediction()

    first = PolicyReplay(
        policy_version_id="MONEY-001-v1",
        starting_capital_yen=10_000,
    ).replay(original, odds={"horse-1": 2.2, "horse-2": 3.0})
    second = PolicyReplay(
        policy_version_id="MONEY-001-v2",
        starting_capital_yen=10_000,
    ).replay(original, odds={"horse-1": 2.2, "horse-2": 3.0})

    assert first.prediction_snapshot_id == original.prediction_snapshot_id
    assert first.prediction_checksum == second.prediction_checksum
    assert first.policy_version_id != second.policy_version_id
    assert original.probabilities == {"horse-1": 0.6, "horse-2": 0.4}


def test_incomplete_odds_keep_prediction_metrics_but_withhold_betting_metrics() -> None:
    evaluation = CoverageAwareEvaluator.evaluate(
        prediction=prediction(),
        actual_winner="horse-1",
        recommendation_decision="SKIP",
        odds_coverage_status="insufficient",
        payout_yen=None,
    )

    assert evaluation.prediction_metrics["top1_correct"] is True
    assert evaluation.betting_metrics is None
    assert evaluation.odds_coverage_status == "insufficient"


def test_complete_odds_make_betting_metrics_available() -> None:
    evaluation = CoverageAwareEvaluator.evaluate(
        prediction=prediction(),
        actual_winner="horse-1",
        recommendation_decision="BUY",
        odds_coverage_status="complete",
        payout_yen=220,
    )

    assert evaluation.prediction_metrics["top1_correct"] is True
    assert evaluation.betting_metrics == {"payout_yen": 220, "profit_yen": 120}

