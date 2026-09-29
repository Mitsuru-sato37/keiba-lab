from decimal import Decimal

from fastapi.testclient import TestClient

from keiba_lab.api.main import create_app
from keiba_lab.application.policy import RecommendationPolicy
from keiba_lab.application.vertical_slice import Phase1Service
from keiba_lab.providers.fixture import FixtureProvider


def client() -> TestClient:
    service = Phase1Service(
        provider=FixtureProvider(), policy=RecommendationPolicy(min_ev=Decimal("1.20"))
    )
    return TestClient(create_app(service=service))


def test_today_and_race_routes_expose_stored_evidence() -> None:
    response = client().get("/races?date=2022-01-01&as_of=2022-01-01T02:30:00Z")
    assert response.status_code == 200
    race_id = response.json()[0]["race_id"]
    detail = client().get(f"/races/{race_id}?as_of=2022-01-01T02:30:00Z")
    assert detail.status_code == 200
    assert detail.json()["recommendation"]["decision"] == "WAIT"
    assert detail.json()["prediction"]["prediction_snapshot_id"].startswith("PRED-")


def test_odds_update_returns_new_recommendation_state() -> None:
    api = client()
    race_id = api.get("/races?date=2022-01-01&as_of=2022-01-01T02:30:00Z").json()[0]["race_id"]
    response = api.post(
        f"/races/{race_id}/odds", json={"odds": "5.0", "calculated_at": "2022-01-01T02:30:00Z"}
    )
    assert response.status_code == 200
    assert response.json()["decision"] == "BUY"
