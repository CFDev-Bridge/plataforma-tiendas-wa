"""Comprobaciones de disponibilidad de dependencias."""

import asyncio
import logging
from typing import Protocol

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine

from app.core.logging import log_fields

logger = logging.getLogger(__name__)

DEFAULT_PROBE_TIMEOUT_SECONDS = 2.0


class ReadinessProbe(Protocol):
    async def is_ready(self) -> bool: ...


class DatabaseProbe:
    """Verifica que la base de datos acepte conexiones y consultas."""

    def __init__(
        self, engine: AsyncEngine, timeout_seconds: float = DEFAULT_PROBE_TIMEOUT_SECONDS
    ) -> None:
        self._engine = engine
        self._timeout_seconds = timeout_seconds

    async def is_ready(self) -> bool:
        try:
            async with asyncio.timeout(self._timeout_seconds):
                await self._ping()
        except (SQLAlchemyError, OSError, TimeoutError) as exc:
            logger.warning("database_unavailable", extra=log_fields(error_type=type(exc).__name__))
            return False
        return True

    async def _ping(self) -> None:
        async with self._engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
