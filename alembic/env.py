import os
import sys

from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.models import Base
from app.models import Event, Ticket, Place, MetadataModel  # noqa: F401

config = context.config
fileConfig(config.config_file_name)
load_dotenv()

database_url = os.getenv(
    "POSTGRES_CONNECTION_STRING",
    "postgresql+asyncpg://postgres:admin@localhost:5433/events_db",
)

print(f"Using database URL: {database_url}")

config.set_main_option("sqlalchemy.url", database_url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = create_async_engine(
        config.get_main_option("sqlalchemy.url"),
        poolclass=pool.NullPool,
        future=True,
    )

    async def async_run() -> None:
        async with connectable.connect() as connection:
            await connection.run_sync(do_run_migrations)

    import asyncio

    asyncio.run(async_run())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
