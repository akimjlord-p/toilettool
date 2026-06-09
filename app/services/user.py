import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.user import UserRepository


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = UserRepository(session)

    async def get_or_create(self, telegram_id: int, username: str | None = None) -> tuple[User, bool]:
        """
        Возвращает (user, created).
        Если юзер уже есть — просто отдаём его.
        Если нет — создаём нового.
        """
        user = await self.repo.get_by_telegram_id(telegram_id)
        if user:
            # Обновляем username если изменился в Telegram
            if username and user.username != username:
                user.username = username
                await self.repo.session.commit()
                await self.repo.session.refresh(user)
            return user, False

        new_user = User(telegram_id=telegram_id, username=username)
        created = await self.repo.create(new_user)
        return created, True

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        return await self.repo.get_by_telegram_id(telegram_id)

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return await self.repo.get_by_id(user_id)

    async def assign_nickname(
        self,
        moderator: User,
        target_telegram_id: int,
        nickname: str,
    ) -> User:
        """Модератор назначает прозвище другому юзеру."""
        if not moderator.is_moderator:
            raise PermissionError("Только модераторы могут назначать прозвища")

        # Проверяем уникальность
        existing = await self.repo.get_by_nickname(nickname)
        if existing and existing.telegram_id != target_telegram_id:
            raise ValueError(f"Прозвище '{nickname}' уже занято")

        target = await self.repo.get_by_telegram_id(target_telegram_id)
        if not target:
            raise ValueError("Пользователь не найден")

        updated = await self.repo.set_nickname(target.id, nickname)
        return updated

    async def set_moderator(self, admin: User, target_telegram_id: int, is_moderator: bool) -> User:
        """Назначить/снять модератора. Только для is_moderator=True пользователей."""
        if not admin.is_moderator:
            raise PermissionError("Недостаточно прав")

        target = await self.repo.get_by_telegram_id(target_telegram_id)
        if not target:
            raise ValueError("Пользователь не найден")

        return await self.repo.set_moderator(target.id, is_moderator)
