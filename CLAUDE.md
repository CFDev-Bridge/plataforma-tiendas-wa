# CLAUDE.md — Reglas permanentes del proyecto

Plataforma SaaS multi-tenant de tiendas virtuales con asistente de IA en WhatsApp.
El contexto completo, el modelo de datos y las fases están en `docs/arquitectura.md`.
Leerlo antes de cualquier cambio de diseño.

## Idioma y forma de trabajo

- Responder, documentar y escribir mensajes de commit en español.
- Identificadores de código (variables, funciones, tablas, columnas) en inglés.
- Trabajar por fases pequeñas. No iniciar una fase sin aprobación explícita del usuario.
- Cada fase termina con pruebas en verde y commits claros (Conventional Commits en español:
  `feat(whatsapp): valida firma X-Hub-Signature-256`).
- No crear cuentas, no contratar servicios ni registrar nada en terceros. Si se necesita algo
  externo, indicar al usuario el paso exacto que debe hacer.
- Entregar código completo: sin placeholders, `TODO` funcionales, `pass` vacíos ni funciones
  sin implementar.
- Si una propuesta del usuario contradice estas reglas o existe una alternativa mejor,
  decirlo con franqueza antes de implementar.
- Datos de demo siempre ficticios. Nunca datos personales reales en seeds, pruebas ni fixtures.

## Invariantes de arquitectura (no negociables)

1. **Tenant desde el servidor.** El tenant se resuelve desde `phone_number_id` (webhook) o desde
   la sesión autenticada (panel). Nunca aceptar `tenant_id` del modelo de IA, del cliente
   de WhatsApp ni del cuerpo de una petición.
2. **Row-Level Security.** Toda tabla de negocio tiene `tenant_id NOT NULL`, RLS habilitado y
   `FORCE ROW LEVEL SECURITY`. El contexto se fija con `SET LOCAL app.tenant_id` por
   transacción. Sin contexto, la política devuelve cero filas (falla cerrada).
3. **Claves foráneas compuestas** `(tenant_id, id)` entre tablas de negocio para impedir
   referencias cruzadas entre tenants.
4. **La IA no es fuente de verdad.** Precios, stock, disponibilidad, pedidos y citas se obtienen
   o modifican solo mediante herramientas del backend. El contexto de cada herramienta
   (`tenant_id`, `contact_id`, `conversation_id`) lo inyecta el servidor, nunca el modelo.
5. **Asistente acotado.** Solo ventas, soporte y citas del negocio. Rechazar cualquier uso como
   IA de propósito general.
6. **Webhook rápido.** Validar firma, persistir, encolar y responder 200. Nada de IA ni de
   llamadas a Meta dentro de la petición del webhook.
7. **Idempotencia.** `UNIQUE` sobre `wamid`; eventos de estado deduplicados por
   `(wamid, status)`; jobs diarios con clave única por fecha.
8. **Modo HUMAN y `paused_until` mandan sobre la IA.** Revalidar el estado de la conversación
   con bloqueo de fila antes de enviar cualquier respuesta generada.
9. **Solo inserción** en `message_status_events`, `ai_runs` y `audit_logs` (sin `UPDATE`/`DELETE`
   a nivel de permisos y trigger).
10. **Proveedores intercambiables** detrás de puertos: `AIProvider`, `WhatsAppConnection`,
    `Notifier`, `Clock`. El dominio no importa SDK de terceros.

## Seguridad

- Consultas siempre parametrizadas (SQLAlchemy con parámetros bind). Prohibido construir SQL
  concatenando texto.
- Validar toda entrada con esquemas Pydantic (backend) y validadores tipados (Angular).
- Angular: no usar `innerHTML` con contenido de mensajes ni `bypassSecurityTrust*`.
- Sesión del panel en cookie `HttpOnly`, `Secure`, `SameSite=Strict` con token CSRF. No guardar
  tokens en `localStorage`.
- Contraseñas con Argon2id.
- Tokens de WhatsApp cifrados con AES-GCM (clave fuera de la base, con `key_id` para rotación).
  En la vía MANUAL son de solo escritura: ningún endpoint los devuelve.
- Ninguna credencial en el código ni en Git. Configuración en `.env` (ignorado) y `.env.example`
  sin valores reales.
- Logs técnicos sin teléfonos ni contenido de mensajes. Para correlacionar, usar IDs internos o
  un hash con sal del `wa_id`.
- Defensa contra prompt injection: el texto del cliente es dato, no instrucción; herramientas
  con lista blanca, argumentos validados y acciones de escritura con confirmación explícita.
- Mínimo privilegio en roles de base de datos: `app_migrator`, `app_runtime`, `app_platform`.
- `PLATFORM_ADMIN` no lee conversaciones salvo con concesión de soporte temporal, justificada
  y auditada.

## Calidad de código

- Python: tipado estricto (`mypy --strict`), `ruff` para lint y formato, `pytest`.
- Angular: `strict: true`, componentes standalone, ESLint.
- SOLID, DRY, KISS. Funciones pequeñas con una sola responsabilidad. Comentarios solo donde
  aporten el porqué.
- Manejo explícito de errores: excepciones de dominio tipadas, sin `except Exception` silencioso.
- Cada caso de uso nuevo lleva pruebas unitarias; cada regla de aislamiento o seguridad lleva
  prueba de integración contra PostgreSQL real.

## Comandos

El usuario solo tiene Docker: todo comando que se le indique debe correr en contenedores.

- Generar `.env`: `docker compose -f compose.setup.yml run --rm init-env` (`--force` para reemplazar;
  luego `docker compose down --volumes`, porque los roles se crean al inicializar el volumen).
- Levantar todo: `docker compose up -d --build --wait`.
- Backend, formato, lint, tipos y unitarias: `docker compose --profile test run --rm --build backend-checks`.
- Backend, integración contra PostgreSQL real: `docker compose --profile test run --rm --build backend-tests`.
- Panel, formato, lint y pruebas: `docker compose --profile test run --rm --build frontend-checks`.
- Escaneo de secretos: `docker run --rm -v "${PWD}:/repo:ro" zricethezav/gitleaks:v8.30.1 git /repo --redact`.
- Fuera de Docker (solo desarrollo): en `backend/`, `uv run ruff format --check . && uv run ruff check . && uv run mypy app tests && uv run pytest`;
  en `frontend/`, `npm run format:check && npm run lint && npm run test:ci && npm run build`.
- Las pruebas de integración llevan `@pytest.mark.integration`; `pytest` sin argumentos las excluye.

## Convenciones del repositorio

- Backend por módulos en `backend/app/modules/<módulo>/` con `router.py`, `service.py` y, cuando
  haya persistencia, `repository.py`. Infraestructura transversal en `backend/app/core/`.
- La API se crea con `create_app(settings)`; las pruebas sustituyen dependencias con
  `app.dependency_overrides`, nunca parcheando módulos.
- Los roles de BD y el esquema `app` se crean en `infra/postgres/init/`; tablas, RLS y permisos van
  en migraciones Alembic (desde la Fase 1).
- Panel: servicios en `frontend/src/app/core/`, funcionalidades en `frontend/src/app/features/`.
  ESLint prohíbe `innerHTML`, `outerHTML` y `bypassSecurityTrust*`.

## Pendientes que no deben asumirse como definitivos

- Tarifa vigente de WhatsApp para Ecuador y cambios anunciados para 2026.
- Quién asume los pagos a Meta en cada tienda.
- Requisitos vigentes de Tech Provider, App Review y Coexistence.
- Pasarela de pago para Ecuador (fuera de la demo).
- Revisión legal de retención de datos según la LOPDP de Ecuador.
