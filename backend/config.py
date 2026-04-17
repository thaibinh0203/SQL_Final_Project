"""Application configuration helpers."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from urllib.parse import quote_plus
import os


ENV_FILE = Path(".env")


def _load_env_file(file_path: Path) -> dict[str, str]:
    """Load a local .env file so development setup stays simple."""

    if not file_path.exists():
        return {}

    values: dict[str, str] = {}
    for raw_line in file_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")

    return values


def _read_setting(name: str, default: str) -> str:
    """Read settings from environment variables with local .env fallback."""

    env_file_values = _load_env_file(ENV_FILE)
    return os.getenv(name, env_file_values.get(name, default))


@dataclass(frozen=True)
class Settings:
    """Holds resolved runtime settings for database-backed application layers."""

    db_host: str
    db_port: int
    db_user: str
    db_password: str
    db_name: str
    db_echo: bool

    @property
    def sqlalchemy_database_url(self) -> str:
        """Build a SQLAlchemy URL for the MySQL connector driver."""

        encoded_password = quote_plus(self.db_password)
        return (
            f"mysql+mysqlconnector://{self.db_user}:{encoded_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings because configuration should be stable per process."""

    db_echo_raw = _read_setting("DB_ECHO", "false").strip().lower()
    return Settings(
        db_host=_read_setting("DB_HOST", "127.0.0.1"),
        db_port=int(_read_setting("DB_PORT", "3306")),
        db_user=_read_setting("DB_USER", "root"),
        db_password=_read_setting("DB_PASSWORD", ""),
        db_name=_read_setting("DB_NAME", "recruitment_management_system"),
        db_echo=db_echo_raw in {"1", "true", "yes", "on"},
    )
