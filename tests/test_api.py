import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from fastapi import Depends, Request

from app.models import Base
from app.models.user import User
from app.repositories.user import UserRepository
from main import app
from app.database import get_session
from app.api.deps import get_current_user, get_moderator

TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5433/toilettool_test"
TEST_BOT_SECRET = "test_secret"

TABLES_TO_TRUNCATE = [
    "toilet_of_month",
    "moderator_reviews",
    "review_photos",
    "reviews",
    "toilets",
    "users",
]

BASE_HEADERS = {
    "x-telegram-id": "100001",
    "x-bot-secret": TEST_BOT_SECRET,
    "x-username": "testuser",
}

MOD_HEADERS = {
    "x-telegram-id": "100002",
    "x-bot-secret": TEST_BOT_SECRET,
    "x-username": "moderator",
}


@pytest_asyncio.fixture
async def test_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        for table in TABLES_TO_TRUNCATE:
            await conn.execute(text(f'TRUNCATE TABLE "{table}" CASCADE'))
    await engine.dispose()


@pytest_asyncio.fixture
async def client(test_engine):
    """
    HTTP-клиент с подменённой БД и bot_secret.
    Все запросы идут через FastAPI напрямую (без сети).
    """
    factory = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_session():
        async with factory() as s:
            yield s

    async def override_get_current_user(
        request: Request,
        session: AsyncSession = Depends(override_get_session),
    ):
        """
        В тестах пропускаем проверку bot_secret.
        Берём telegram_id прямо из заголовка запроса.
        """
        from fastapi import HTTPException
        bot_secret = request.headers.get("x-bot-secret", "")
        if bot_secret != TEST_BOT_SECRET:
            raise HTTPException(status_code=403, detail="Invalid bot secret")

        telegram_id = int(request.headers.get("x-telegram-id", "100001"))
        username = request.headers.get("x-username")

        from app.services.user import UserService
        svc = UserService(session)
        user, _ = await svc.get_or_create(telegram_id=telegram_id, username=username)
        return user

    async def override_get_moderator(
        user: User = Depends(override_get_current_user),
    ):
        from fastapi import HTTPException
        if not user.is_moderator:
            raise HTTPException(status_code=403, detail="Moderator access required")
        return user

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_moderator] = override_get_moderator

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def moderator_client(test_engine, client):
    """Создаёт модератора и возвращает клиент + заголовки модератора."""
    factory = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as s:
        repo = UserRepository(s)
        from app.services.user import UserService
        svc = UserService(s)
        mod, _ = await svc.get_or_create(telegram_id=100002, username="moderator")
        await repo.set_moderator(mod.id, True)
    return client, MOD_HEADERS


# ─── /health ───────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_health(client):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


# ─── /users ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_me(client):
    r = await client.get("/api/v1/users/me", headers=BASE_HEADERS)
    assert r.status_code == 200
    data = r.json()
    assert data["telegram_id"] == 100001
    assert data["is_moderator"] is False


@pytest.mark.asyncio
async def test_get_me_wrong_secret(client):
    r = await client.get("/api/v1/users/me", headers={**BASE_HEADERS, "x-bot-secret": "wrong"})
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_assign_nickname_as_moderator(moderator_client):
    client, mod_headers = moderator_client
    # Сначала создаём целевого пользователя
    await client.get("/api/v1/users/me", headers=BASE_HEADERS)
    r = await client.post(
        "/api/v1/users/nickname",
        headers=mod_headers,
        json={"target_telegram_id": 100001, "nickname": "Великий ревизор"},
    )
    assert r.status_code == 200
    assert r.json()["nickname"] == "Великий ревизор"


@pytest.mark.asyncio
async def test_assign_nickname_not_moderator(client):
    r = await client.post(
        "/api/v1/users/nickname",
        headers=BASE_HEADERS,
        json={"target_telegram_id": 100001, "nickname": "Самозванец"},
    )
    assert r.status_code == 403


# ─── /toilets ──────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_toilet(client):
    r = await client.post(
        "/api/v1/toilets",
        headers=BASE_HEADERS,
        json={"address": "ул. Пушкина, 10", "name": "ТЦ Пушкин"},
    )
    assert r.status_code == 201
    data = r.json()
    assert data["address"] == "ул. Пушкина, 10"
    assert "id" in data


@pytest.mark.asyncio
async def test_search_toilets_found(client):
    await client.post(
        "/api/v1/toilets",
        headers=BASE_HEADERS,
        json={"address": "ул. Лесная, 5"},
    )
    r = await client.get("/api/v1/toilets/search?q=Лесная")
    assert r.status_code == 200
    data = r.json()
    assert data["needs_creation"] is False
    assert len(data["found"]) >= 1


@pytest.mark.asyncio
async def test_search_toilets_not_found(client):
    r = await client.get("/api/v1/toilets/search?q=НесуществующаяУлица999")
    assert r.status_code == 200
    assert r.json()["needs_creation"] is True


@pytest.mark.asyncio
async def test_get_toilet_card(client):
    created = await client.post(
        "/api/v1/toilets",
        headers=BASE_HEADERS,
        json={"address": "пр. Карточный, 1"},
    )
    toilet_id = created.json()["id"]

    r = await client.get(f"/api/v1/toilets/{toilet_id}")
    assert r.status_code == 200
    data = r.json()
    assert data["toilet"]["id"] == toilet_id
    assert data["avg_scores"] is None  # отзывов ещё нет


@pytest.mark.asyncio
async def test_get_toilet_not_found(client):
    import uuid
    r = await client.get(f"/api/v1/toilets/{uuid.uuid4()}")
    assert r.status_code == 404


# ─── /reviews ──────────────────────────────────────────────────────────────────

REVIEW_PAYLOAD = {
    "score_cleanliness": 20,
    "score_supplies": 15,
    "score_smell": 18,
    "score_equipment": 12,
    "score_privacy": 4,
    "score_vibe": 4,
    "comment": "Весьма достойно",
}


@pytest.mark.asyncio
async def test_create_review(client):
    toilet = await client.post(
        "/api/v1/toilets", headers=BASE_HEADERS, json={"address": "ул. Отзывная, 1"}
    )
    toilet_id = toilet.json()["id"]

    r = await client.post(
        "/api/v1/reviews",
        headers=BASE_HEADERS,
        json={**REVIEW_PAYLOAD, "toilet_id": toilet_id},
    )
    assert r.status_code == 201
    data = r.json()
    assert data["total_score"] == 20 + 15 + 18 + 12 + 4 + 4
    assert data["comment"] == "Весьма достойно"


@pytest.mark.asyncio
async def test_no_duplicate_review(client):
    toilet = await client.post(
        "/api/v1/toilets", headers=BASE_HEADERS, json={"address": "ул. Дубль, 2"}
    )
    toilet_id = toilet.json()["id"]

    await client.post(
        "/api/v1/reviews",
        headers=BASE_HEADERS,
        json={**REVIEW_PAYLOAD, "toilet_id": toilet_id},
    )
    r = await client.post(
        "/api/v1/reviews",
        headers=BASE_HEADERS,
        json={**REVIEW_PAYLOAD, "toilet_id": toilet_id},
    )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_invalid_score(client):
    toilet = await client.post(
        "/api/v1/toilets", headers=BASE_HEADERS, json={"address": "ул. Неверная, 3"}
    )
    toilet_id = toilet.json()["id"]

    r = await client.post(
        "/api/v1/reviews",
        headers=BASE_HEADERS,
        json={**REVIEW_PAYLOAD, "toilet_id": toilet_id, "score_cleanliness": 99},
    )
    assert r.status_code == 422  # Pydantic validation error


@pytest.mark.asyncio
async def test_delete_review_as_moderator(moderator_client):
    client, mod_headers = moderator_client

    toilet = await client.post(
        "/api/v1/toilets", headers=BASE_HEADERS, json={"address": "ул. Удаляемая, 4"}
    )
    toilet_id = toilet.json()["id"]

    review = await client.post(
        "/api/v1/reviews",
        headers=BASE_HEADERS,
        json={**REVIEW_PAYLOAD, "toilet_id": toilet_id},
    )
    review_id = review.json()["id"]

    r = await client.request(
        "DELETE",
        f"/api/v1/reviews/{review_id}",
        headers=mod_headers,
        json={"reason": "Нарушение правил"},
    )
    assert r.status_code == 200
    assert r.json()["is_deleted"] is True


# ─── /top ──────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_top_empty(client):
    r = await client.get("/api/v1/top")
    assert r.status_code == 200
    assert r.json() == []


@pytest.mark.asyncio
async def test_get_top_with_data(client):
    toilet = await client.post(
        "/api/v1/toilets", headers=BASE_HEADERS, json={"address": "ул. Топовая, 1"}
    )
    toilet_id = toilet.json()["id"]
    await client.post(
        "/api/v1/reviews",
        headers=BASE_HEADERS,
        json={**REVIEW_PAYLOAD, "toilet_id": toilet_id},
    )

    r = await client.get("/api/v1/top?criterion=total")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    assert data[0]["toilet"]["id"] == toilet_id


@pytest.mark.asyncio
async def test_get_top_invalid_criterion(client):
    r = await client.get("/api/v1/top?criterion=nonexistent")
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_toilet_of_month_empty(client):
    r = await client.get("/api/v1/top/month")
    assert r.status_code == 200
    assert r.json() is None


# ─── photos ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_review_with_photos(client):
    """Отзыв с фото принимается, photos возвращаются в ответе."""
    toilet = await client.post(
        "/api/v1/toilets", headers=BASE_HEADERS, json={"address": "ул. Фото, 1"}
    )
    toilet_id = toilet.json()["id"]

    r = await client.post(
        "/api/v1/reviews",
        headers=BASE_HEADERS,
        json={
            **REVIEW_PAYLOAD,
            "toilet_id": toilet_id,
            "photos": ["AgACAgIxxx1", "AgACAgIxxx2"],
        },
    )
    assert r.status_code == 201
    data = r.json()
    assert data["photos"] == ["AgACAgIxxx1", "AgACAgIxxx2"]


@pytest.mark.asyncio
async def test_create_review_too_many_photos(client):
    """Больше 3 фото — ошибка валидации."""
    toilet = await client.post(
        "/api/v1/toilets", headers=BASE_HEADERS, json={"address": "ул. Много фото, 2"}
    )
    toilet_id = toilet.json()["id"]

    r = await client.post(
        "/api/v1/reviews",
        headers=BASE_HEADERS,
        json={
            **REVIEW_PAYLOAD,
            "toilet_id": toilet_id,
            "photos": ["fid1", "fid2", "fid3", "fid4"],
        },
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_create_review_no_photos(client):
    """Отзыв без фото — photos пустой список."""
    toilet = await client.post(
        "/api/v1/toilets", headers=BASE_HEADERS, json={"address": "ул. Без фото, 3"}
    )
    toilet_id = toilet.json()["id"]

    r = await client.post(
        "/api/v1/reviews",
        headers=BASE_HEADERS,
        json={**REVIEW_PAYLOAD, "toilet_id": toilet_id},
    )
    assert r.status_code == 201
    assert r.json()["photos"] == []
