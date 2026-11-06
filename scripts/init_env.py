"""Genera el archivo .env a partir de .env.example con contraseñas aleatorias.

Uso (desde la raíz del repositorio):
    python scripts/init_env.py            # crea .env si no existe
    python scripts/init_env.py --force    # lo reemplaza (las contraseñas de un volumen
                                          # de PostgreSQL ya inicializado dejan de coincidir)
Solo usa la biblioteca estándar.
"""

import argparse
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
    if TARGET_FILE.exists() and not args.force:
        print(f"{TARGET_FILE.name} ya existe; usa --force para reemplazarlo.", file=sys.stderr)
        return 1
    example_lines = EXAMPLE_FILE.read_text(encoding="utf-8").splitlines()
    TARGET_FILE.write_text("\n".join(render_env(example_lines)) + "\n", encoding="utf-8")
    TARGET_FILE.chmod(0o600)
    print(f"{TARGET_FILE.name} generado con contraseñas aleatorias.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
