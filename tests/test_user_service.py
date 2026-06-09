import pytest

from app.models.user import User
from app.repositories.user import UserRepository
from app.services.user import UserService


async def _force_make_moderator(session, telegram_id: int) -> User:
    """Напрямую назначает модератора в обход проверки прав — только для тестов."""
    repo = UserRepository(session)
    user = await repo.get_by_telegram_id(telegram_id)
    return await repo.set_moderator(user.id, True)


@pytest.mark.asyncio
async def test_get_or_create_new_user(session):
    """Новый пользователь создаётся при первом обращении."""
    service = UserService(session)
    user, created = await service.get_or_create(telegram_id=111, username="vasya")

    assert created is True
    assert user.telegram_id == 111
    assert user.username == "vasya"
    assert user.is_moderator is False


@pytest.mark.asyncio
async def test_get_or_create_existing_user(session):
    """Повторный вызов не создаёт дубль."""
    service = UserService(session)
    user1, _ = await service.get_or_create(telegram_id=222, username="petya")
    user2, created = await service.get_or_create(telegram_id=222, username="petya")

    assert created is False
    assert user1.id == user2.id


@pytest.mark.asyncio
async def test_username_updates_on_login(session):
    """Если username изменился в Telegram — обновляем."""
    service = UserService(session)
    await service.get_or_create(telegram_id=333, username="old_name")
    user, created = await service.get_or_create(telegram_id=333, username="new_name")

    assert created is False
    assert user.username == "new_name"


@pytest.mark.asyncio
async def test_assign_nickname(session):
    """Модератор может назначить прозвище другому юзеру."""
    service = UserService(session)

    moderator, _ = await service.get_or_create(telegram_id=1001)
    moderator = await _force_make_moderator(session, 1001)

    target, _ = await service.get_or_create(telegram_id=1002)

    updated = await service.assign_nickname(moderator, 1002, "Гуру унитаза")
    assert updated.nickname == "Гуру унитаза"


@pytest.mark.asyncio
async def test_assign_nickname_not_moderator(session):
    """Обычный юзер не может назначить прозвище."""
    service = UserService(session)
    user, _ = await service.get_or_create(telegram_id=2001)
    target, _ = await service.get_or_create(telegram_id=2002)

    with pytest.raises(PermissionError):
        await service.assign_nickname(user, 2002, "Тест")


@pytest.mark.asyncio
async def test_assign_duplicate_nickname(session):
    """Два юзера не могут иметь одинаковое прозвище."""
    service = UserService(session)

    mod, _ = await service.get_or_create(telegram_id=3001)
    mod = await _force_make_moderator(session, 3001)

    await service.get_or_create(telegram_id=3002)
    await service.get_or_create(telegram_id=3003)

    await service.assign_nickname(mod, 3002, "Уникальное имя")

    with pytest.raises(ValueError, match="уже занято"):
        await service.assign_nickname(mod, 3003, "Уникальное имя")
