import asyncio
import sys
from pathlib import Path
from typing import AsyncGenerator, Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Добавить родительскую директорию в path для импорта модуля 'app'
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import Base, get_session
from app.main import app

pytest_plugins = ("pytest_asyncio",)


DATABASE_URL = "sqlite+aiosqlite:///./test_wallets.db"
engine = create_async_engine(
    DATABASE_URL,
    future=True,
    echo=False,
    connect_args={"check_same_thread": False},
)
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


@pytest.fixture(scope="session", autouse=True)
def prepare_database():  # Подготовка базы данных
    async def init_db() -> None:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(init_db())
    yield
    asyncio.run(engine.dispose())


@pytest.fixture(autouse=True)
def override_db() -> Generator[None, None, None]:  # Переопределение БД
    app.dependency_overrides[get_session] = override_get_session
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    client = TestClient(app)
    yield client
