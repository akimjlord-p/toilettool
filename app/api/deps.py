from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_session
from app.models.user import User
from app.services.user import UserService


async def get_db(session: AsyncSession = Depends(get_session)) -> AsyncSession:
    return session


async def get_current_user(
    x_telegram_id: Annotated[int, Header()],
    x_bot_secret: Annotated[str, Header()],
    session: AsyncSession = Depends(get_db),
    x_username: Annotated[str | None, Header()] = None,
) -> User:
    """
    Каждый запрос от бота приходит с заголовками:
      X-Telegram-Id: 123456789
      X-Username: nickname (опционально)
      X-Bot-Secret: секретный ключ для проверки что запрос от нашего бота
    """
    if x_bot_secret != settings.bot_secret:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid bot secret")

    service = UserService(session)
    user, _ = await service.get_or_create(
        telegram_id=x_telegram_id,
        username=x_username,
    )
    return user


async def get_moderator(user: User = Depends(get_current_user)) -> User:
    """Используется в эндпоинтах только для модераторов."""
    if not user.is_moderator:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Moderator access required")
    return user


# Удобные алиасы для Depends
DbSession = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]
ModeratorUser = Annotated[User, Depends(get_moderator)]
