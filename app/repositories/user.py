import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

    async def get_by_nickname(self, nickname: str) -> User | None:
        result = await self.session.execute(
            select(User).where(User.nickname == nickname)
        )
        return result.scalar_one_or_none()

    async def set_nickname(self, user_id: uuid.UUID, nickname: str | None) -> User | None:
        user = await self.get_by_id(user_id)
        if not user:
            return None
        user.nickname = nickname
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def set_moderator(self, user_id: uuid.UUID, is_moderator: bool) -> User | None:
        user = await self.get_by_id(user_id)
        if not user:
            return None
        user.is_moderator = is_moderator
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def add_balance(self, user_id: uuid.UUID, amount: int) -> None:
        await self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(balance=User.balance + amount)
        )
        await self.session.commit()

    async def get_token_top(self, limit: int = 10) -> list[User]:
        result = await self.session.execute(
            select(User)
            .where(User.balance > 0)
            .order_by(User.balance.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
