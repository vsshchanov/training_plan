import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Подставляем переменные окружения в URL
section = config.config_ini_section
config.set_section_option(section, "POSTGRES_USER",     os.environ.get("POSTGRES_USER", "postgres"))
config.set_section_option(section, "POSTGRES_PASSWORD", os.environ.get("POSTGRES_PASSWORD", "postgres"))
config.set_section_option(section, "POSTGRES_HOST",     os.environ.get("POSTGRES_HOST", "localhost"))
config.set_section_option(section, "POSTGRES_PORT",     os.environ.get("POSTGRES_PORT", "5432"))
config.set_section_option(section, "POSTGRES_DB",       os.environ.get("POSTGRES_DB", "workout_tracker"))

from storage.postgres_storage import Base
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata,
                      literal_binds=True, dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
