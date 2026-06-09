import pytest

from app.services.toilet import ToiletService
from app.services.user import UserService


async def _make_user(session, telegram_id=9999):
    service = UserService(session)
    user, _ = await service.get_or_create(telegram_id=telegram_id)
    return user


@pytest.mark.asyncio
async def test_create_toilet(session):
    """Туалет создаётся с нужными полями."""
    user = await _make_user(session, 10001)
    service = ToiletService(session)

    toilet = await service.create(
        address="ул. Ленина, 1",
        created_by=user,
        name="ТЦ Центральный, 1 этаж",
    )

    assert toilet.id is not None
    assert toilet.address == "ул. Ленина, 1"
    assert toilet.name == "ТЦ Центральный, 1 этаж"
    assert toilet.created_by_id == user.id


@pytest.mark.asyncio
async def test_search_by_address(session):
    """Поиск находит туалет по части адреса."""
    user = await _make_user(session, 10002)
    service = ToiletService(session)

    await service.create(address="пр. Победы, 42", created_by=user)
    await service.create(address="пр. Мира, 10", created_by=user)

    results = await service.search_by_address("Победы")
    assert len(results) == 1
    assert results[0].address == "пр. Победы, 42"


@pytest.mark.asyncio
async def test_search_too_short(session):
    """Поиск по строке меньше 3 символов возвращает пустой список."""
    service = ToiletService(session)
    results = await service.search_by_address("пр")
    assert results == []


@pytest.mark.asyncio
async def test_find_or_suggest_found(session):
    """find_or_suggest возвращает кандидатов если нашёл."""
    user = await _make_user(session, 10003)
    service = ToiletService(session)

    await service.create(address="ул. Советская, 5", created_by=user)
    result = await service.find_or_suggest("Советская")

    assert result["needs_creation"] is False
    assert len(result["found"]) >= 1


@pytest.mark.asyncio
async def test_find_or_suggest_not_found(session):
    """find_or_suggest сигнализирует о необходимости создать туалет."""
    service = ToiletService(session)
    result = await service.find_or_suggest("Несуществующая улица 999")

    assert result["needs_creation"] is True
    assert result["found"] == []


@pytest.mark.asyncio
async def test_get_card_not_found(session):
    """get_card возвращает None для несуществующего туалета."""
    import uuid
    service = ToiletService(session)
    card = await service.get_card(uuid.uuid4())
    assert card is None
