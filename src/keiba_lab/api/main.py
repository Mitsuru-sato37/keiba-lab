from fastapi import FastAPI

from keiba_lab.settings import Settings, get_settings


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved = settings or get_settings()
    application = FastAPI(title="keiba-lab API", version=resolved.api_version)

    @application.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "keiba-lab-api", "version": resolved.api_version}

    return application


app = create_app()
