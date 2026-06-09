import uuid
from datetime import datetime

from pydantic import BaseModel


class UserResponse(BaseModel):
    id: uuid.UUID
    telegram_id: int
    username: str | None
    nickname: str | None
    is_moderator: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class AssignNicknameRequest(BaseModel):
    target_telegram_id: int
    nickname: str


class SetModeratorRequest(BaseModel):
    target_telegram_id: int
    is_moderator: bool
