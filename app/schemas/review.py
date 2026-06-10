import uuid
from datetime import datetime

from pydantic import BaseModel, field_validator


class ReviewCreate(BaseModel):
    toilet_id: uuid.UUID
    score_cleanliness: int
    score_supplies: int
    score_smell: int
    score_equipment: int
    score_privacy: int
    score_vibe: int
    comment: str | None = None
    photos: list[str] = []  # до 3 Telegram file_id

    @field_validator("photos")
    def check_photos(cls, v):
        assert len(v) <= 3, "Максимум 3 фото"
        return v

    @field_validator("score_cleanliness")
    def check_cleanliness(cls, v):
        assert 0 <= v <= 25, "score_cleanliness: 0–25"
        return v

    @field_validator("score_supplies")
    def check_supplies(cls, v):
        assert 0 <= v <= 20, "score_supplies: 0–20"
        return v

    @field_validator("score_smell")
    def check_smell(cls, v):
        assert 0 <= v <= 20, "score_smell: 0–20"
        return v

    @field_validator("score_equipment")
    def check_equipment(cls, v):
        assert 0 <= v <= 15, "score_equipment: 0–15"
        return v

    @field_validator("score_privacy")
    def check_privacy(cls, v):
        assert 0 <= v <= 5, "score_privacy: 0–5"
        return v

    @field_validator("score_vibe")
    def check_vibe(cls, v):
        assert 0 <= v <= 5, "score_vibe: 0–5"
        return v


class ReviewResponse(BaseModel):
    id: uuid.UUID
    toilet_id: uuid.UUID
    user_id: uuid.UUID
    score_cleanliness: int
    score_supplies: int
    score_smell: int
    score_equipment: int
    score_privacy: int
    score_vibe: int
    total_score: int
    comment: str | None
    is_deleted: bool
    photos: list[str] = []
    created_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_with_photos(cls, review) -> "ReviewResponse":
        obj = cls.model_validate(review)
        obj.photos = [p.file_id for p in (review.photos or [])]
        return obj


class DeleteReviewRequest(BaseModel):
    reason: str


class ModeratorReviewResponse(ReviewResponse):
    moderator_id: uuid.UUID
    is_official: bool
