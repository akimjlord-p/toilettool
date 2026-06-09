import uuid
from datetime import datetime

from pydantic import BaseModel

from app.schemas.toilet import ToiletResponse


class TopEntry(BaseModel):
    toilet: ToiletResponse
    avg_score: float
    review_count: int


class ToiletOfMonthResponse(BaseModel):
    id: uuid.UUID
    toilet: ToiletResponse
    year: int
    month: int
    avg_score: float
    ai_comment: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
