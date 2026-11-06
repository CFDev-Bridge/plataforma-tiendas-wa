import logging

import pytest

from app.core.middleware import REQUEST_ID_HEADER, SECURITY_HEADERS
from tests.conftest import ClientFactory, StubProbe


def test_live_returns_ok(client_factory: ClientFactory) -> None:
    response = client_factory().get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_returns_ok_when_database_is_available(client_factory: ClientFactory) -> None:
    response = client_factory(probe=StubProbe(ready=True)).get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "checks": {"database": "ok"}}


def test_ready_returns_503_when_database_is_unavailable(client_factory: ClientFactory) -> None:
    response = client_factory(probe=StubProbe(ready=False)).get("/health/ready")

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable", "checks": {"database": "unavailable"}}


def test_responses_include_security_headers(client_factory: ClientFactory) -> None:
    response = client_factory().get("/health/live")

    for name, value in SECURITY_HEADERS.items():
        assert response.headers[name] == value


def test_request_id_is_generated_by_server_and_ignores_client_value(
    client_factory: ClientFactory,
) -> None:
    response = client_factory().get(
        "/health/live", headers={REQUEST_ID_HEADER: "valor-inyectado-por-cliente"}
    )

    request_id = response.headers[REQUEST_ID_HEADER]
    assert request_id != "valor-inyectado-por-cliente"
    assert len(request_id) == 32


def test_access_log_omits_query_string(
    client_factory: ClientFactory, caplog: pytest.LogCaptureFixture
) -> None:
    client = client_factory()
    caplog.set_level(logging.INFO, logger="app.access")

    client.get("/health/live", params={"hub.verify_token": "secreto-que-no-debe-aparecer"})

    access_records = [record for record in caplog.records if record.name == "app.access"]
    assert access_records, "se esperaba un registro de acceso"
    assert all(
        "secreto-que-no-debe-aparecer" not in record.getMessage() for record in caplog.records
    )
    assert all(
        "secreto-que-no-debe-aparecer" not in str(getattr(record, "fields", ""))
        for record in access_records
    )
