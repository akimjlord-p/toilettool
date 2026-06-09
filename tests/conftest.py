import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models import Base

TEST_DATABASE_URL = "postgresql+asyncpg://toilettool:tt_secret_2024@147.45.107.85:5432/toilettool_test"

TABLES_TO_TRUNCATE = [
    "toilet_of_month",
    "moderator_reviews",
    "reviews",
    "toilets",
    "users",
]


@pytest_asyncio.fixture
async def session():
    """
    Каждый тест получает свой engine и сессию.
    После теста — очищаем таблицы.
    """
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    # Создаём таблицы если не существуют
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with factory() as s:
        yield s

    # Очищаем данные после теста
    async with engine.begin() as conn:
        for table in TABLES_TO_TRUNCATE:
            await conn.execute(text(f'TRUNCATE TABLE "{table}" CASCADE'))

    await engine.dispose()
