import uuid

from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, UUIDMixin, TimestampMixin


class Toilet(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "toilets"

    address: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str | None] = mapped_column(String(500), nullable=True)
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lon: Mapped[float | None] = mapped_column(Float, nullable=True)
    yandex_place_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_by_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    creator: Mapped["User"] = relationship("User", back_populates="toilets", foreign_keys=[created_by_id])
    reviews: Mapped[list["Review"]] = relationship("Review", back_populates="toilet")
    moderator_reviews: Mapped[list["ModeratorReview"]] = relationship("ModeratorReview", back_populates="toilet")
