from datetime import UTC, date, datetime
from decimal import Decimal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from keiba_lab.application.policy import RecommendationPolicy
from keiba_lab.application.vertical_slice import Phase1Service
from keiba_lab.providers.fixture import FixtureProvider
from keiba_lab.settings import Settings, get_settings


class OddsUpdate(BaseModel):
    odds: Decimal = Field(gt=0)
    calculated_at: datetime


def create_app(settings: Settings | None = None, service: Phase1Service | None = None) -> FastAPI:
    resolved = settings or get_settings()
    resolved_service = service or Phase1Service(
        provider=FixtureProvider(), policy=RecommendationPolicy()
    )
    application = FastAPI(title="keiba-lab API", version=resolved.api_version)

    @application.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "keiba-lab-api", "version": resolved.api_version}

    @application.get("/races")
    def list_races(date: date, as_of: datetime | None = None) -> list[dict[str, object]]:
        moment = as_of or datetime.now(UTC)
        return [item.model_dump(mode="json") for item in resolved_service.list_today(date, moment)]

    @application.get("/races/{race_id}")
    def get_race(race_id: str, as_of: datetime | None = None) -> dict[str, object]:
        try:
            detail = resolved_service.get_race(race_id, as_of or datetime.now(UTC))
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="race not found") from exc
        return detail.model_dump(mode="json")

    @application.post("/races/{race_id}/odds")
    def update_odds(race_id: str, payload: OddsUpdate) -> dict[str, object]:
        try:
            recommendation = resolved_service.update_odds(
                race_id, payload.odds, payload.calculated_at
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="race not found") from exc
        return recommendation.model_dump(mode="json")

    return application


app = create_app()
