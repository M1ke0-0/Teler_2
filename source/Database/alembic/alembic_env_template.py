"""
Шаблон для source/Database/alembic/env.py

Используй этот файл при инициализации Alembic:
cd source/Database
alembic init alembic

Затем замени содержимое alembic/env.py на этот шаблон.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Загружаем .env из корня проекта
env_path = Path(__file__).resolve().parents[3] / '.env'
if env_path.exists():
    load_dotenv(env_path)

# Импортируем Base из наших моделей
from source.Database.database import Base

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object for 'autogenerate' support
target_metadata = Base.metadata

# Строка подключения из переменных окружения
def get_sqlalchemy_url():
    """Получить строку подключения к БД из переменных окружения"""
    db_user = os.getenv('POSTGRES_USER', 'telerag_user')
    db_password = os.getenv('POSTGRES_PASSWORD', 'telerag_password')
    db_host = os.getenv('POSTGRES_HOST', 'localhost')
    db_port = os.getenv('POSTGRES_PORT', '5432')
    db_name = os.getenv('POSTGRES_DB', 'telerag_db')
    
    return f'postgresql+asyncpg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = get_sqlalchemy_url()
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

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    url = get_sqlalchemy_url()
    
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = url
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        echo=False,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
