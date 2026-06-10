import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models import Base

TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5433/toilettool_test"

TABLES_TO_TRUNCATE = [
    "toilet_of_month",
    "moderator_reviews",
    "review_photos",
    "reviews",
    "toilets",
    "users",
]


@pytest.fixture(autouse=True)
def mock_geocoder():
    """Отключаем Яндекс геокодер в тестах — он нам не нужен."""
    with patch("app.services.geocoder.YandexGeocoder.geocode", new_callable=AsyncMock, return_value=None):
        yield


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
