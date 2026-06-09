from sqlalchemy import BigInteger, Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, UUIDMixin, TimestampMixin


class User(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "users"

    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    nickname: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True)
    is_moderator: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    toilets: Mapped[list["Toilet"]] = relationship("Toilet", back_populates="creator", foreign_keys="Toilet.created_by_id")
    reviews: Mapped[list["Review"]] = relationship("Review", back_populates="user", foreign_keys="Review.user_id")
    moderator_reviews: Mapped[list["ModeratorReview"]] = relationship("ModeratorReview", back_populates="moderator")
