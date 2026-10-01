from fastapi import APIRouter
from keiba_domain.health import HealthStatus
from keiba_infrastructure.settings import Settings


def health_router(settings: Settings) -> APIRouter:
    router = APIRouter(prefix="/health")

    @router.get("/live")
    def live() -> dict[str, str]:
        return {"status": HealthStatus.OK.value, "service": settings.app_name}

    @router.get("/ready")
    def ready() -> dict[str, object]:
        return {
            "status": HealthStatus.OK.value,
            "service": settings.app_name,
            "dependencies": {
                "jra_van": "configured" if settings.jra_van_enabled else "not_configured",
                "postgres": "configured" if settings.database_url else "not_configured",
            },
        }

    return router
