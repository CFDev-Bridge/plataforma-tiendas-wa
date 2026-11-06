from collections.abc import Callable, Iterator

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.core.config import AppEnv, Settings
from app.main import create_app
from app.modules.health.router import get_readiness_probe
from app.modules.health.service import ReadinessProbe


class StubProbe:
    def __init__(self, ready: bool) -> None:
        self.ready = ready

    async def is_ready(self) -> bool:
        return self.ready


def build_settings(app_env: AppEnv = AppEnv.TEST) -> Settings:
    return Settings(
        app_env=app_env,
        db_host="db.invalid",
        db_name="tiendas_test",
        db_user="app_runtime",
        db_password=SecretStr("contrasena-ficticia"),
    )


ClientFactory = Callable[..., TestClient]


@pytest.fixture
def client_factory() -> Iterator[ClientFactory]:
    clients: list[TestClient] = []

    def factory(probe: ReadinessProbe | None = None, app_env: AppEnv = AppEnv.TEST) -> TestClient:
        app = create_app(build_settings(app_env))
        resolved_probe = probe if probe is not None else StubProbe(ready=True)
        app.dependency_overrides[get_readiness_probe] = lambda: resolved_probe
        client = TestClient(app)
        client.__enter__()
        clients.append(client)
        return client

    yield factory
    for client in clients:
        client.__exit__(None, None, None)
