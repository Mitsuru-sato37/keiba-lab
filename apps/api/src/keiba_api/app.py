from fastapi import FastAPI
from keiba_infrastructure.settings import Settings

from .health import health_router


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved_settings = settings or Settings()
    app = FastAPI(title=resolved_settings.app_name, version="0.1.0")
    app.include_router(health_router(resolved_settings))
    return app
