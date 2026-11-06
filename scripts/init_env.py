"""Genera el archivo .env a partir de .env.example con contraseñas aleatorias.

Se ejecuta dentro de Docker, sin Python en la máquina anfitriona (desde la raíz del repositorio):
    docker compose -f compose.setup.yml run --rm init-env            # crea .env si no existe
    docker compose -f compose.setup.yml run --rm init-env --force    # lo reemplaza
Al reemplazarlo, las contraseñas de un volumen de PostgreSQL ya inicializado dejan de coincidir.
Solo usa la biblioteca estándar.
"""

import argparse
import os
import secrets
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EXAMPLE_FILE = REPO_ROOT / ".env.example"
TARGET_FILE = REPO_ROOT / ".env"

SECRET_KEYS = frozenset(
    {
        "POSTGRES_SUPERUSER_PASSWORD",
        "APP_MIGRATOR_DB_PASSWORD",
        "APP_RUNTIME_DB_PASSWORD",
        "APP_PLATFORM_DB_PASSWORD",
    }
)
SECRET_BYTES = 32


def generate_secret() -> str:
    # token_urlsafe solo produce [A-Za-z0-9_-]: seguro en URLs y en variables de entorno.
    return secrets.token_urlsafe(SECRET_BYTES)


def render_env(example_lines: list[str]) -> list[str]:
    rendered: list[str] = []
    for line in example_lines:
        key, separator, value = line.partition("=")
        is_assignment = separator and not line.lstrip().startswith("#")
        if is_assignment and key.strip() in SECRET_KEYS and not value.strip():
            rendered.append(f"{key}={generate_secret()}")
        else:
            rendered.append(line)
    return rendered


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--force", action="store_true", help="reemplaza un .env existente")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    replacing = TARGET_FILE.exists()
    if replacing and not args.force:
        print(f"{TARGET_FILE.name} ya existe; usa --force para reemplazarlo.", file=sys.stderr)
        return 1
    example_lines = EXAMPLE_FILE.read_text(encoding="utf-8").splitlines()
    TARGET_FILE.write_text("\n".join(render_env(example_lines)) + "\n", encoding="utf-8")
    TARGET_FILE.chmod(0o600)
    give_ownership_to_repository_owner(TARGET_FILE)
    print(f"{TARGET_FILE.name} generado con contraseñas aleatorias.")
    if replacing:
        print(
            "Aviso: si PostgreSQL ya se inicializó, recrea su volumen para aplicar las nuevas "
            "contraseñas (se borran los datos): docker compose down --volumes",
            file=sys.stderr,
        )
    return 0


def give_ownership_to_repository_owner(path: Path) -> None:
    # Dentro de un contenedor el script corre como root; en Linux el .env quedaría ilegible
    # para el usuario que ejecuta `docker compose`. Se asigna al dueño del repositorio.
    if not hasattr(os, "geteuid") or os.geteuid() != 0:
        return
    owner = REPO_ROOT.stat()
    os.chown(path, owner.st_uid, owner.st_gid)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
