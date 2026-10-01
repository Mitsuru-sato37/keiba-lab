from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="KEIBA_", extra="ignore")

    app_name: str = "keiba-lab-api"
    environment: str = "local"
    timezone: str = "Asia/Tokyo"
    database_url: str | None = None
    jra_van_enabled: bool = False
    jra_van_use_key: SecretStr | None = None
