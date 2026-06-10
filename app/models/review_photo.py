import uuid

from sqlalchemy import ForeignKey, SmallInteger, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, UUIDMixin, TimestampMixin


class ReviewPhoto(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "review_photos"

    review_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reviews.id"), nullable=False, index=True
    )
    file_id: Mapped[str] = mapped_column(String(255), nullable=False)  # Telegram file_id
    position: Mapped[int] = mapped_column(SmallInteger, nullable=False)  # 1, 2, 3

    review: Mapped["Review"] = relationship("Review", back_populates="photos")
