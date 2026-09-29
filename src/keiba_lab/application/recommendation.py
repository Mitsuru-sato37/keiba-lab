from collections.abc import Mapping
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from keiba_lab.application.policy import RecommendationPolicy


class WinRecommendation(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    decision: str
    reason_codes: tuple[str, ...]
    fair_odds: Decimal | None = None
    expected_value: Decimal | None = None
    policy_version: str
    prediction_snapshot_id: str = Field(min_length=1)
    odds: Decimal | None = None


def evaluate_win_recommendation(
    prediction: Mapping[str, object], current_odds: Decimal | None, policy: RecommendationPolicy
) -> WinRecommendation:
    probability = prediction["win_probability"]
    uncertainty = prediction["uncertainty"]
    if not isinstance(probability, Decimal) or not isinstance(uncertainty, Decimal):
        raise TypeError("prediction probabilities must be Decimal")
    snapshot_id = prediction["prediction_snapshot_id"]
    if not isinstance(snapshot_id, str) or not snapshot_id:
        raise ValueError("prediction snapshot ID is required")
    if current_odds is None:
        return WinRecommendation(
            decision="WAIT",
            reason_codes=("ODDS_UNAVAILABLE",),
            policy_version=policy.policy_version,
            prediction_snapshot_id=snapshot_id,
        )
    if current_odds <= 0:
        raise ValueError("current odds must be positive")
    if uncertainty > policy.max_uncertainty:
        return WinRecommendation(
            decision="SKIP",
            reason_codes=("SKIP_UNRELIABLE",),
            policy_version=policy.policy_version,
            prediction_snapshot_id=snapshot_id,
            odds=current_odds,
        )
    fair_odds = Decimal("1") / probability
    expected_value = probability * current_odds
    if expected_value >= policy.min_ev:
        decision, reasons = "BUY", ("POSITIVE_EV",)
    else:
        decision, reasons = "SKIP", ("SKIP_NO_VALUE",)
    return WinRecommendation(
        decision=decision,
        reason_codes=reasons,
        fair_odds=fair_odds,
        expected_value=expected_value,
        policy_version=policy.policy_version,
        prediction_snapshot_id=snapshot_id,
        odds=current_odds,
    )
