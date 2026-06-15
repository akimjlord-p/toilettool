from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser, DbSession, ModeratorUser
from app.repositories.user import UserRepository
from app.schemas.user import AssignNicknameRequest, SetModeratorRequest, TokenTopEntry, UserResponse
from app.services.user import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_me(user: CurrentUser):
    """Получить профиль текущего пользователя."""
    return user


@router.post("/nickname", response_model=UserResponse)
async def assign_nickname(
    body: AssignNicknameRequest,
    moderator: ModeratorUser,
    session: DbSession,
):
    """Модератор назначает прозвище пользователю."""
    service = UserService(session)
    try:
        updated = await service.assign_nickname(
            moderator=moderator,
            target_telegram_id=body.target_telegram_id,
            nickname=body.nickname,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return updated


@router.get("/tokens/top", response_model=list[TokenTopEntry])
async def get_token_top(session: DbSession, limit: int = 10):
    """Топ пользователей по балансу токенов."""
    repo = UserRepository(session)
    users = await repo.get_token_top(limit=min(limit, 50))
    return [
        TokenTopEntry(
            telegram_id=u.telegram_id,
            username=u.username,
            nickname=u.nickname,
            balance=u.balance,
            rank=i + 1,
        )
        for i, u in enumerate(users)
    ]


@router.post("/set-moderator", response_model=UserResponse)
async def set_moderator(
    body: SetModeratorRequest,
    moderator: ModeratorUser,
    session: DbSession,
):
    """Назначить или снять модератора."""
    service = UserService(session)
    try:
        updated = await service.set_moderator(
            admin=moderator,
            target_telegram_id=body.target_telegram_id,
            is_moderator=body.is_moderator,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return updated
