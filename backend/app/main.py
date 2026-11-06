"""Punto de entrada de la API. Se ejecuta con `uvicorn app.main:create_app --factory`."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import Settings, get_settings
from app.core.db import create_database_engine
from app.core.logging import configure_logging
from app.core.middleware import register_middlewares
from app.modules.health.router import router as health_router
from app.modules.health.service import DatabaseProbe

API_TITLE = "Plataforma de tiendas con asistente de WhatsApp"


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved = settings if settings is not None else get_settings()
    configure_logging(resolved.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine = create_database_engine(resolved)
        app.state.readiness_probe = DatabaseProbe(engine)
        try:
            yield
        finally:
            await engine.dispose()

    docs_enabled = resolved.api_docs_enabled
    app = FastAPI(
        title=API_TITLE,
        lifespan=lifespan,
        docs_url="/docs" if docs_enabled else None,
        redoc_url=None,
        openapi_url="/openapi.json" if docs_enabled else None,
    )
    register_middlewares(app)
    app.include_router(health_router)
    return app
