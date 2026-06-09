import uuid
from datetime import datetime

from pydantic import BaseModel


class ToiletCreate(BaseModel):
    address: str
    name: str | None = None
    lat: float | None = None
    lon: float | None = None
    yandex_place_id: str | None = None


class ToiletResponse(BaseModel):
    id: uuid.UUID
    address: str
    name: str | None
    lat: float | None
    lon: float | None
    yandex_place_id: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class AvgScores(BaseModel):
    cleanliness: float
    supplies: float
    smell: float
    equipment: float
    privacy: float
    vibe: float
    total: float
    review_count: int


class ToiletCard(BaseModel):
    toilet: ToiletResponse
    avg_scores: AvgScores | None


class ToiletSearchResponse(BaseModel):
    found: list[ToiletResponse]
    needs_creation: bool
