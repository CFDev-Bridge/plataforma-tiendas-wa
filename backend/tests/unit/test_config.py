import pytest
from pydantic import SecretStr, ValidationError

from app.core.config import AppEnv, Settings
from tests.conftest import ClientFactory, build_settings


def test_database_url_does_not_expose_password_in_its_representation() -> None:
    settings = build_settings()

    assert "contrasena-ficticia" not in str(settings.database_url)
    assert "contrasena-ficticia" not in repr(settings)


def test_database_url_escapes_special_characters_in_password() -> None:
    settings = build_settings().model_copy(update={"db_password": SecretStr("p@ss:/word")})

    rendered = settings.database_url.render_as_string(hide_password=False)

    assert "p%40ss%3A%2Fword" in rendered


def test_rejects_unknown_environment() -> None:
    with pytest.raises(ValidationError):
        Settings(
            app_env="staging",  # type: ignore[arg-type]
            db_host="db.invalid",
            db_name="tiendas_test",
            db_user="app_runtime",
            db_password="contrasena-ficticia",  # type: ignore[arg-type]
        )


def test_rejects_out_of_range_port() -> None:
    with pytest.raises(ValidationError):
        Settings(
            app_env=AppEnv.TEST,
            db_host="db.invalid",
            db_port=70000,
            db_name="tiendas_test",
            db_user="app_runtime",
            db_password="contrasena-ficticia",  # type: ignore[arg-type]
        )


def test_reads_values_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "demo")
    monkeypatch.setenv("DB_HOST", "postgres")
    monkeypatch.setenv("DB_NAME", "tiendas")
    monkeypatch.setenv("DB_USER", "app_runtime")
    monkeypatch.setenv("DB_PASSWORD", "contrasena-ficticia")

    settings = Settings()

    assert settings.app_env is AppEnv.DEMO
    assert settings.db_host == "postgres"
    assert settings.db_password.get_secret_value() == "contrasena-ficticia"


def test_api_docs_are_disabled_in_production(client_factory: ClientFactory) -> None:
    client = client_factory(app_env=AppEnv.PRODUCTION)

    assert client.get("/docs").status_code == 404
    assert client.get("/openapi.json").status_code == 404


def test_api_docs_are_enabled_in_demo(client_factory: ClientFactory) -> None:
    client = client_factory(app_env=AppEnv.DEMO)

    assert client.get("/openapi.json").status_code == 200
