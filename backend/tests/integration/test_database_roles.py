import pytest
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError

from app.modules.health.service import DatabaseProbe
from tests.integration.conftest import (
    APPLICATION_ROLES,
    MIGRATOR,
    PLATFORM,
    RUNTIME,
    EngineFactory,
    RoleCredentials,
)

pytestmark = pytest.mark.integration


async def test_database_probe_is_ready_with_runtime_role(engine_factory: EngineFactory) -> None:
    probe = DatabaseProbe(engine_factory(RUNTIME))

    assert await probe.is_ready() is True


async def test_database_probe_is_not_ready_with_wrong_password(
    engine_factory: EngineFactory,
) -> None:
    probe = DatabaseProbe(engine_factory(RUNTIME, password="contrasena-incorrecta"))

    assert await probe.is_ready() is False


@pytest.mark.parametrize("role", APPLICATION_ROLES, ids=lambda role: role.user)
async def test_application_roles_have_no_elevated_attributes(
    engine_factory: EngineFactory, role: RoleCredentials
) -> None:
    query = text(
        "SELECT rolsuper, rolcreatedb, rolcreaterole, rolreplication, rolbypassrls "
        "FROM pg_roles WHERE rolname = :role_name"
    )
    async with engine_factory(role).connect() as connection:
        attributes = (await connection.execute(query, {"role_name": role.user})).one()

    assert not any(attributes)


CREATE_TABLE_STATEMENTS = {
    "app": "CREATE TABLE app.privilege_probe (id integer)",
    "public": "CREATE TABLE public.privilege_probe (id integer)",
}


@pytest.mark.parametrize("role", [RUNTIME, PLATFORM], ids=lambda role: role.user)
@pytest.mark.parametrize("schema", sorted(CREATE_TABLE_STATEMENTS))
async def test_application_roles_cannot_create_objects(
    engine_factory: EngineFactory, role: RoleCredentials, schema: str
) -> None:
    statement = text(CREATE_TABLE_STATEMENTS[schema])

    async with engine_factory(role).connect() as connection:
        with pytest.raises(ProgrammingError, match="permission denied"):
            await connection.execute(statement)


async def test_migrator_owns_application_schema(engine_factory: EngineFactory) -> None:
    query = text("SELECT nspowner::regrole::text FROM pg_namespace WHERE nspname = 'app'")

    async with engine_factory(MIGRATOR).connect() as connection:
        owner = (await connection.execute(query)).scalar_one()

    assert owner == MIGRATOR.user


@pytest.mark.parametrize("role", APPLICATION_ROLES, ids=lambda role: role.user)
async def test_application_roles_default_to_app_schema(
    engine_factory: EngineFactory, role: RoleCredentials
) -> None:
    async with engine_factory(role).connect() as connection:
        search_path = (await connection.execute(text("SHOW search_path"))).scalar_one()

    assert search_path == "app"
