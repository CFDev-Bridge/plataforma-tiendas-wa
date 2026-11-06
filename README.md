# Plataforma de tiendas con asistente de WhatsApp

Plataforma SaaS multi-tenant de tiendas virtuales con asistente de IA en WhatsApp. Cada negocio se
agrega por configuración. Arquitectura, modelo de datos y fases: [`docs/arquitectura.md`](docs/arquitectura.md).
Reglas del proyecto: [`CLAUDE.md`](CLAUDE.md).

> Estado: **Fase 0** (base del proyecto). La demo usa exclusivamente datos ficticios.

## Requisitos

Solo **Docker**: Docker Desktop (Windows o macOS) o Docker Engine con Compose v2 (Linux), y Git.
No necesitas Python ni Node en tu máquina: todo, incluidas las pruebas, corre en contenedores.

Los comandos son iguales en PowerShell, CMD, bash y zsh. Ejecútalos desde la raíz del repositorio.

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
   docker compose -f compose.setup.yml run --rm init-env
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

Todos los puertos se publican solo en `127.0.0.1`. Si alguno está ocupado, cámbialo en `.env`.

## Pruebas

Backend: formato, lint, tipos y pruebas unitarias:

```bash
docker compose --profile test run --rm --build backend-checks
```

Backend: pruebas de integración contra PostgreSQL real (levanta la base si no está arriba):

```bash
docker compose --profile test run --rm --build backend-tests
```

Panel: formato, lint y pruebas:

```bash
docker compose --profile test run --rm --build frontend-checks
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

Borrar también la base de datos:

```bash
docker compose down --volumes
```

Regenerar el `.env`. Los roles de PostgreSQL se crean solo al inicializar el volumen, así que
después hay que borrarlo con el comando anterior para que tomen las nuevas contraseñas:

```bash
docker compose -f compose.setup.yml run --rm init-env --force
```

## Desarrollo sin Docker (opcional)

Solo si quieres editar con recarga en caliente. Requiere [uv](https://docs.astral.sh/uv/) para el
backend y Node 24 para el panel; los comandos están en [`CLAUDE.md`](CLAUDE.md#comandos).

## Seguridad

- Ninguna credencial va en el código ni en Git. `.env` está en `.gitignore`.
- La API se conecta con el rol `app_runtime`, sin privilegios de superusuario ni `BYPASSRLS`.
- Los contenedores corren sin root, con sistema de archivos de solo lectura y sin capacidades
  de Linux, salvo donde se indica en `docker-compose.yml`.
- CI ejecuta un escaneo de secretos con gitleaks. Para hacerlo en local:

  ```bash
  docker run --rm -v "%cd%:/repo:ro" zricethezav/gitleaks:v8.30.1 git /repo --redact
  ```

  En CMD se usa `%cd%`; en PowerShell, bash o zsh, reemplázalo por `${PWD}`.
