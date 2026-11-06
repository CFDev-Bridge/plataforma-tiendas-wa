# syntax=docker/dockerfile:1

ARG PYTHON_IMAGE=python:3.13-slim
ARG UV_VERSION=0.13.7

# Dependencias de ejecución en un entorno virtual aislado.
FROM ${PYTHON_IMAGE} AS deps
ARG UV_VERSION
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/opt/venv
RUN pip install --no-cache-dir "uv==${UV_VERSION}"
WORKDIR /build
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Imagen de pruebas: añade dependencias de desarrollo y el código de pruebas.
FROM deps AS test
RUN uv sync --frozen --no-install-project
WORKDIR /srv
COPY pyproject.toml ./
COPY app ./app
COPY tests ./tests
RUN groupadd --system app && useradd --system --gid app --no-create-home app
USER app
# Cachés en /tmp: el contenedor de pruebas corre con sistema de archivos de solo lectura.
ENV PATH="/opt/venv/bin:${PATH}" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    RUFF_CACHE_DIR=/tmp/ruff-cache \
    MYPY_CACHE_DIR=/tmp/mypy-cache \
    PYTEST_ADDOPTS="-p no:cacheprovider"
CMD ["pytest", "-m", "integration"]

# Imagen de ejecución mínima, sin herramientas de construcción y con usuario sin privilegios.
FROM ${PYTHON_IMAGE} AS runtime
RUN groupadd --system app && useradd --system --gid app --no-create-home app
COPY --from=deps /opt/venv /opt/venv
WORKDIR /srv
COPY app ./app
USER app
ENV PATH="/opt/venv/bin:${PATH}" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--no-access-log", "--no-server-header"]
