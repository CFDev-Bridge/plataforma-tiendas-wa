"""Fixtures para pruebas contra PostgreSQL real.

Usan las mismas variables que Docker Compose. Se ejecutan con:
    docker compose --profile test run --rm backend-tests
"""

import os
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass

import pytest
from pydantic import SecretStr
from sqlalchemy.ext.asyncio import AsyncEngine

from app.core.config import AppEnv, Settings
from app.core.db import create_database_engine


@dataclass(frozen=True)
class RoleCredentials:
    user: str
    password_variable: str


RUNTIME = RoleCredentials("app_runtime", "APP_RUNTIME_DB_PASSWORD")
PLATFORM = RoleCredentials("app_platform", "APP_PLATFORM_DB_PASSWORD")
MIGRATOR = RoleCredentials("app_migrator", "APP_MIGRATOR_DB_PASSWORD")
APPLICATION_ROLES = (RUNTIME, PLATFORM, MIGRATOR)


def _required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        pytest.fail(f"Falta la variable de entorno {name} para las pruebas de integración.")
    return value


def settings_for(role: RoleCredentials, password: str | None = None) -> Settings:
    return Settings(
        app_env=AppEnv.TEST,
        db_host=_required_env("DB_HOST"),
        db_port=int(os.environ.get("DB_PORT", "5432")),
        db_name=_required_env("POSTGRES_DB"),
        db_user=role.user,
        db_password=SecretStr(password or _required_env(role.password_variable)),
    )


EngineFactory = Callable[..., AsyncEngine]


@pytest.fixture
async def engine_factory() -> AsyncIterator[EngineFactory]:
    engines: list[AsyncEngine] = []

    def factory(role: RoleCredentials, password: str | None = None) -> AsyncEngine:
        engine = create_database_engine(settings_for(role, password))
        engines.append(engine)
        return engine

    yield factory
    for engine in engines:
        await engine.dispose()
