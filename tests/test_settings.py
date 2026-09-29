from pydantic import SecretStr

from keiba_lab.settings import Settings


def test_settings_have_safe_local_defaults() -> None:
    settings = Settings()
    assert settings.environment == "development"
    assert settings.timezone == "Asia/Tokyo"
    assert settings.database_url.get_secret_value().startswith("postgresql+")


def test_settings_repr_redacts_database_url() -> None:
    settings = Settings(database_url=SecretStr("postgresql+psycopg://user:secret@host/db"))
    assert "secret" not in repr(settings)
