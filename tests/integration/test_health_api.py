import httpx
import pytest


@pytest.mark.anyio
async def test_live_health_reports_process_liveness() -> None:
    from keiba_api.app import create_app

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=create_app()),
        base_url="http://test",
    ) as client:
        response = await client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "keiba-lab-api"}


@pytest.mark.anyio
async def test_ready_health_does_not_require_optional_services() -> None:
    from keiba_api.app import create_app

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=create_app()),
        base_url="http://test",
    ) as client:
        response = await client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "keiba-lab-api",
        "dependencies": {"jra_van": "not_configured", "postgres": "not_configured"},
    }
