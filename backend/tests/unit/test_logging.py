import json
import logging
import sys

from app.core.logging import JsonFormatter, configure_logging, log_fields, request_id_var


def _make_record(message: str, **kwargs: object) -> logging.LogRecord:
    return logging.LogRecord(
        name="app.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg=message,
        args=(),
        exc_info=kwargs.pop("exc_info", None),  # type: ignore[arg-type]
    )


def test_formats_record_as_json_with_structured_fields() -> None:
    record = _make_record("evento")
    for key, value in log_fields(status=200, path="/health/live").items():
        setattr(record, key, value)

    payload = json.loads(JsonFormatter().format(record))

    assert payload["msg"] == "evento"
    assert payload["level"] == "INFO"
    assert payload["status"] == 200
    assert payload["path"] == "/health/live"


def test_includes_request_id_from_context() -> None:
    token = request_id_var.set("abc123")
    try:
        payload = json.loads(JsonFormatter().format(_make_record("evento")))
    finally:
        request_id_var.reset(token)

    assert payload["request_id"] == "abc123"


def test_configure_logging_is_idempotent_and_keeps_foreign_handlers() -> None:
    root = logging.getLogger()
    foreign = logging.NullHandler()
    root.addHandler(foreign)
    try:
        configure_logging("INFO")
        configure_logging("INFO")

        app_handlers = [h for h in root.handlers if isinstance(h.formatter, JsonFormatter)]
        assert len(app_handlers) == 1
        assert foreign in root.handlers
        assert logging.getLogger("httpx2").level == logging.WARNING
        assert logging.getLogger("uvicorn.access").disabled
    finally:
        root.removeHandler(foreign)


def _raise_value_error(message: str) -> None:
    raise ValueError(message)


def test_exception_logs_type_and_frames_but_not_message() -> None:
    sensitive_text = "+593000000000 hola quiero comprar"
    try:
        _raise_value_error(sensitive_text)
    except ValueError:
        record = _make_record("fallo", exc_info=sys.exc_info())

    output = JsonFormatter().format(record)
    payload = json.loads(output)

    assert payload["exc_type"] == "ValueError"
    assert payload["exc_frames"]
    assert sensitive_text not in output
