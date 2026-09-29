from datetime import UTC, datetime
from decimal import Decimal

from keiba_lab.application.policy import RecommendationPolicy
from keiba_lab.application.vertical_slice import Phase1Service
from keiba_lab.providers.fixture import FixtureProvider


def service() -> Phase1Service:
    return Phase1Service(
        provider=FixtureProvider(), policy=RecommendationPolicy(min_ev=Decimal("1.20"))
    )


def test_fixture_flow_keeps_prediction_immutable_when_odds_change() -> None:
    app = service()
    as_of = datetime(2022, 1, 1, 2, 30, tzinfo=UTC)
    races = app.list_today(datetime(2022, 1, 1), as_of)
    assert races[0].race_id == "R202201010101"
    first = app.get_race(races[0].race_id, as_of)
    assert first.recommendation.decision == "WAIT"
    first_prediction = first.prediction
    bought = app.update_odds(first.race_id, Decimal("5.0"), as_of)
    assert bought.decision == "BUY"
    changed = app.update_odds(first.race_id, Decimal("3.0"), as_of)
    assert changed.decision == "SKIP"
    assert app.get_race(first.race_id, as_of).prediction == first_prediction
    assert len(app.recommendations(first.race_id)) == 3


def test_phase1_service_has_no_purchase_or_result_access() -> None:
    assert not hasattr(Phase1Service, "purchase")
    assert not hasattr(Phase1Service, "get_result")
