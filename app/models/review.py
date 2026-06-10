import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, SmallInteger, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, UUIDMixin, TimestampMixin


class Review(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "reviews"
    __table_args__ = (UniqueConstraint("toilet_id", "user_id", name="uq_review_toilet_user"),)

    toilet_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("toilets.id"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    score_cleanliness: Mapped[int] = mapped_column(SmallInteger, nullable=False)  # 0–25
    score_supplies: Mapped[int] = mapped_column(SmallInteger, nullable=False)     # 0–20
    score_smell: Mapped[int] = mapped_column(SmallInteger, nullable=False)        # 0–20
    score_equipment: Mapped[int] = mapped_column(SmallInteger, nullable=False)    # 0–15
    score_privacy: Mapped[int] = mapped_column(SmallInteger, nullable=False)      # 0–5
    score_vibe: Mapped[int] = mapped_column(SmallInteger, nullable=False)         # 0–5
    total_score: Mapped[int] = mapped_column(SmallInteger, nullable=False)        # 0–90

    comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deleted_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    deleted_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    toilet: Mapped["Toilet"] = relationship("Toilet", back_populates="reviews")
    user: Mapped["User"] = relationship("User", back_populates="reviews", foreign_keys=[user_id])
    deleted_by: Mapped["User | None"] = relationship("User", foreign_keys=[deleted_by_id])
    photos: Mapped[list["ReviewPhoto"]] = relationship("ReviewPhoto", back_populates="review", order_by="ReviewPhoto.position")
