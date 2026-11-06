"""Creación del motor asíncrono de base de datos."""

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.core.config import Settings

APPLICATION_NAME = "plataforma-tiendas-api"


def create_database_engine(settings: Settings) -> AsyncEngine:
    return create_async_engine(
        settings.database_url,
        pool_size=settings.db_pool_size,
        pool_pre_ping=True,
        connect_args={
            "timeout": settings.db_connect_timeout_seconds,
            "server_settings": {"application_name": APPLICATION_NAME},
        },
    )
