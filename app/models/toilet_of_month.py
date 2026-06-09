import uuid

from sqlalchemy import ForeignKey, Numeric, SmallInteger, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, UUIDMixin, TimestampMixin


class ToiletOfMonth(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "toilet_of_month"
    __table_args__ = (UniqueConstraint("year", "month", name="uq_toilet_of_month_year_month"),)

    toilet_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("toilets.id"), nullable=False)
    year: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    month: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    avg_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    ai_comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    toilet: Mapped["Toilet"] = relationship("Toilet")
