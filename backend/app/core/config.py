"""Configuración de la aplicación leída exclusivamente desde variables de entorno."""

from enum import StrEnum
from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR"]


class AppEnv(StrEnum):
    DEMO = "demo"
    TEST = "test"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """Parámetros de ejecución. No lee archivos .env: el entorno los inyecta explícitamente."""

    model_config = SettingsConfigDict(extra="ignore", frozen=True)

    app_env: AppEnv
    log_level: LogLevel = "INFO"

    db_host: str = Field(min_length=1, max_length=255)
    db_port: int = Field(default=5432, ge=1, le=65535)
    db_name: str = Field(min_length=1, max_length=63)
    db_user: str = Field(min_length=1, max_length=63)
    db_password: SecretStr = Field(min_length=1)
    db_pool_size: int = Field(default=5, ge=1, le=50)
    db_connect_timeout_seconds: float = Field(default=5.0, gt=0, le=60)

    @property
    def database_url(self) -> URL:
        # URL.create escapa caracteres especiales y su representación oculta la contraseña.
        return URL.create(
            drivername="postgresql+asyncpg",
            username=self.db_user,
            password=self.db_password.get_secret_value(),
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
        )

    @property
    def api_docs_enabled(self) -> bool:
        return self.app_env is not AppEnv.PRODUCTION


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
