from keiba_infrastructure.settings import Settings
from pydantic import SecretStr


def test_settings_have_local_safe_defaults() -> None:
    settings = Settings()

    assert settings.app_name == "keiba-lab-api"
    assert settings.environment == "local"
    assert settings.jra_van_enabled is False
    assert settings.database_url is None


def test_settings_can_receive_explicit_dependency_configuration() -> None:
    settings = Settings(
        database_url="postgresql://localhost/keiba_lab",
        jra_van_enabled=True,
        jra_van_use_key=SecretStr("test-only-secret"),
    )

    assert settings.database_url is not None
    assert settings.jra_van_enabled is True
    assert settings.jra_van_use_key is not None
    assert settings.jra_van_use_key.get_secret_value() == "test-only-secret"
