from fastapi.testclient import TestClient

from keiba_lab.api.main import create_app
from keiba_lab.settings import Settings


def test_health_exposes_no_configuration_secrets() -> None:
    settings = Settings(database_url="postgresql+psycopg://user:secret@host/db")
    response = TestClient(create_app(settings)).get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "keiba-lab-api", "version": "0.1.0"}
    assert "secret" not in response.text
