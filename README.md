# Plataforma de tiendas con asistente de WhatsApp

Plataforma SaaS multi-tenant de tiendas virtuales con asistente de IA en WhatsApp. Cada negocio se
agrega por configuración. Arquitectura, modelo de datos y fases: [`docs/arquitectura.md`](docs/arquitectura.md).
Reglas del proyecto: [`CLAUDE.md`](CLAUDE.md).

> Estado: **Fase 0** (base del proyecto). La demo usa exclusivamente datos ficticios.

## Requisitos

- Docker Desktop (Windows o macOS) o Docker Engine con Compose v2 (Linux).
- Python 3.10 o superior, solo para generar el `.env`. Si no lo tienes, ver la alternativa abajo.

## Primer arranque

1. Clona el repositorio y entra en la carpeta:

   ```bash
   git clone https://github.com/CFDev-Bridge/plataforma-tiendas-wa.git
   ```

   ```bash
   cd plataforma-tiendas-wa
   ```

2. Genera el `.env` con contraseñas aleatorias (no se sube a Git):

   ```bash
   python scripts/init_env.py
   ```

   Sin Python instalado, ejecútalo dentro de un contenedor (PowerShell, bash o zsh):

   ```bash
   docker run --rm -v "${PWD}:/w" -w /w python:3.13-slim python scripts/init_env.py
   ```

3. Construye y levanta los servicios:

   ```bash
   docker compose up -d --build --wait
   ```

| Servicio | URL (solo en tu máquina) |
|---|---|
| Panel | http://127.0.0.1:8080 |
| API (documentación interactiva, solo en `demo`) | http://127.0.0.1:8000/docs |
| Estado de la API | http://127.0.0.1:8080/health/ready |
| Mailpit (correos capturados) | http://127.0.0.1:8025 |
| PostgreSQL | `127.0.0.1:5432`, base `tiendas` |

Todos los puertos se publican solo en `127.0.0.1`. Se cambian en `.env` si están ocupados.

## Pruebas

Pruebas de integración contra PostgreSQL real (con los servicios levantados):

```bash
docker compose --profile test run --rm --build backend-tests
```

Backend fuera de Docker (requiere [uv](https://docs.astral.sh/uv/)):

```bash
cd backend && uv sync && uv run ruff check . && uv run mypy app tests && uv run pytest
```

Panel fuera de Docker (requiere Node 24):

```bash
cd frontend && npm ci && npm run lint && npm run test:ci && npm run build
```

## Operación

Ver logs de la API:

```bash
docker compose logs -f api
```

Detener los servicios conservando los datos:

```bash
docker compose down
```

Borrar también la base de datos (necesario si regeneras el `.env`, porque los roles se crean solo
al inicializar el volumen):

```bash
docker compose down --volumes
```

## Seguridad

- Ninguna credencial va en el código ni en Git. `.env` está en `.gitignore`.
- Escaneo de secretos en CI con gitleaks. Opcionalmente, en local:

  ```bash
  pip install pre-commit && pre-commit install
  ```

- La API se conecta con el rol `app_runtime`, sin privilegios de superusuario ni `BYPASSRLS`.
