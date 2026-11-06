"""Logs técnicos en JSON.

Política: nunca registrar teléfonos ni contenido de mensajes. Por eso las excepciones se
registran por tipo y ubicación, sin su mensaje, que puede contener datos de entrada.
"""

import json
import logging
import sys
import traceback
from collections.abc import Mapping
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any

from app.core.config import LogLevel

request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)

_FIELDS_ATTRIBUTE = "fields"
_APP_HANDLER_NAME = "app-json"
_UVICORN_LOGGERS = ("uvicorn", "uvicorn.error", "uvicorn.access")
_URL_LOGGING_CLIENTS = ("httpx", "httpx2", "httpcore")


def log_fields(**fields: str | int | float | bool | None) -> dict[str, Mapping[str, Any]]:
    """Construye el argumento `extra` para adjuntar campos estructurados a un log."""
    return {_FIELDS_ATTRIBUTE: fields}


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        request_id = request_id_var.get()
        if request_id is not None:
            payload["request_id"] = request_id
        fields = getattr(record, _FIELDS_ATTRIBUTE, None)
        if isinstance(fields, Mapping):
            payload.update(fields)
        if record.exc_info and record.exc_info[0] is not None:
            payload["exc_type"] = record.exc_info[0].__name__
            payload["exc_frames"] = _describe_frames(record.exc_info[2])
        return json.dumps(payload, ensure_ascii=False, default=str)


def _describe_frames(tb: Any) -> list[str]:
    return [
        f"{frame.filename}:{frame.lineno} in {frame.name}" for frame in traceback.extract_tb(tb)
    ]


def configure_logging(level: LogLevel) -> None:
    """Instala el handler JSON en el logger raíz. Es idempotente y no toca handlers ajenos."""
    root = logging.getLogger()
    root.handlers = [h for h in root.handlers if h.get_name() != _APP_HANDLER_NAME]
    root.addHandler(_build_json_handler())
    root.setLevel(level)

    for name in _UVICORN_LOGGERS:
        uvicorn_logger = logging.getLogger(name)
        uvicorn_logger.handlers.clear()
        uvicorn_logger.propagate = True
    # El access log de uvicorn incluye la query string (p. ej. hub.verify_token): se reemplaza
    # por el middleware de acceso propio, que solo registra la ruta.
    logging.getLogger("uvicorn.access").disabled = True
    # Los clientes HTTP registran la URL completa en INFO, con posibles datos sensibles.
    for name in _URL_LOGGING_CLIENTS:
        logging.getLogger(name).setLevel(logging.WARNING)


def _build_json_handler() -> logging.Handler:
    handler = logging.StreamHandler(sys.stdout)
    handler.set_name(_APP_HANDLER_NAME)
    handler.setFormatter(JsonFormatter())
    return handler
