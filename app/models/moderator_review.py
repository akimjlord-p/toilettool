import uuid

from sqlalchemy import Boolean, ForeignKey, SmallInteger, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, UUIDMixin, TimestampMixin


class ModeratorReview(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "moderator_reviews"
    __table_args__ = (UniqueConstraint("toilet_id", "moderator_id", name="uq_mod_review_toilet_moderator"),)

    toilet_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("toilets.id"), nullable=False)
    moderator_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    score_cleanliness: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    score_supplies: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    score_smell: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    score_equipment: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    score_privacy: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    score_vibe: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    total_score: Mapped[int] = mapped_column(SmallInteger, nullable=False)

    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_official: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    toilet: Mapped["Toilet"] = relationship("Toilet", back_populates="moderator_reviews")
    moderator: Mapped["User"] = relationship("User", back_populates="moderator_reviews")
