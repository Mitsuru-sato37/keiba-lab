from functools import lru_cache
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="KEIBA_", env_file=".env", extra="ignore")

    environment: Literal["development", "test", "production"] = "development"
    timezone: Literal["Asia/Tokyo"] = "Asia/Tokyo"
    database_url: SecretStr = SecretStr(
        "postgresql+psycopg://keiba:keiba_local@localhost:5432/keiba_lab"
    )
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    api_version: str = "0.1.0"


@lru_cache
def get_settings() -> Settings:
    return Settings()
