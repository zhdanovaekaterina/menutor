"""Alembic environment configuration.

Reads DATABASE_URL from .config/.env (production) or falls back to
sqlite:///data/menutor.db (local development).
"""

import os
import sys
from logging.config import fileConfig
from pathlib import Path

# Ensure project root is on sys.path so "backend" package is importable
_project_root = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_project_root))

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool

from backend.infrastructure.database.models import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# Load DATABASE_URL from .config/.env relative to project root
_project_root = Path(__file__).resolve().parents[4]
_env_path = _project_root / ".config" / ".env"
load_dotenv(_env_path)

_db_url = os.environ.get("DATABASE_URL", "sqlite:///data/menutor.db")
config.set_main_option("sqlalchemy.url", _db_url)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    Generates SQL script without connecting to the database.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    Creates an engine and connects to the database.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
