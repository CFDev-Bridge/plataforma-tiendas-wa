#!/bin/sh
# Crea los roles de aplicación con mínimo privilegio y el esquema `app`.
# Se ejecuta una sola vez, al inicializar un volumen de datos vacío.
# Las contraseñas llegan por variables de entorno y se pasan a psql como variables
# (:'nombre'), que psql cita de forma segura; nunca se concatenan en el SQL.
set -eu

: "${APP_MIGRATOR_DB_PASSWORD:?Falta APP_MIGRATOR_DB_PASSWORD}"
: "${APP_RUNTIME_DB_PASSWORD:?Falta APP_RUNTIME_DB_PASSWORD}"
: "${APP_PLATFORM_DB_PASSWORD:?Falta APP_PLATFORM_DB_PASSWORD}"

psql --no-psqlrc -v ON_ERROR_STOP=1 \
  --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
  -v db_name="$POSTGRES_DB" \
  -v migrator_password="$APP_MIGRATOR_DB_PASSWORD" \
  -v runtime_password="$APP_RUNTIME_DB_PASSWORD" \
  -v platform_password="$APP_PLATFORM_DB_PASSWORD" <<'SQL'
-- Dueño del esquema; solo lo usan las migraciones.
CREATE ROLE app_migrator LOGIN PASSWORD :'migrator_password'
  NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;

-- API y worker: sujetos a Row-Level Security.
CREATE ROLE app_runtime LOGIN PASSWORD :'runtime_password'
  NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS NOINHERIT;

-- Administración de plataforma y jobs: acceso entre tenants mediante políticas explícitas.
CREATE ROLE app_platform LOGIN PASSWORD :'platform_password'
  NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS NOINHERIT;

REVOKE ALL ON DATABASE :"db_name" FROM PUBLIC;
GRANT CONNECT, TEMPORARY ON DATABASE :"db_name" TO app_migrator, app_runtime, app_platform;

REVOKE ALL ON SCHEMA public FROM PUBLIC;
CREATE SCHEMA app AUTHORIZATION app_migrator;
GRANT USAGE ON SCHEMA app TO app_runtime, app_platform;

ALTER ROLE app_migrator SET search_path = app;
ALTER ROLE app_runtime SET search_path = app;
ALTER ROLE app_platform SET search_path = app;

-- Corta consultas o transacciones colgadas de la aplicación.
ALTER ROLE app_runtime SET statement_timeout = '15s';
ALTER ROLE app_runtime SET idle_in_transaction_session_timeout = '30s';
ALTER ROLE app_platform SET statement_timeout = '60s';
ALTER ROLE app_platform SET idle_in_transaction_session_timeout = '60s';
SQL
