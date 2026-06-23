import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.review import Review
from app.repositories.base import BaseRepository


class ReviewRepository(BaseRepository[Review]):
    model = Review

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_id(self, id: uuid.UUID) -> Review | None:
        result = await self.session.execute(
            select(Review).where(Review.id == id).options(selectinload(Review.photos))
        )
        return result.scalar_one_or_none()

    async def get_by_user_and_toilet(self, user_id: uuid.UUID, toilet_id: uuid.UUID) -> Review | None:
        result = await self.session.execute(
            select(Review)
            .where(Review.user_id == user_id, Review.toilet_id == toilet_id)
            .options(selectinload(Review.photos))
        )
        return result.scalar_one_or_none()

    async def count_by_toilet(self, toilet_id: uuid.UUID) -> int:
        result = await self.session.execute(
            select(func.count(Review.id))
            .where(Review.toilet_id == toilet_id, Review.is_deleted == False)
        )
        return result.scalar_one()

    async def get_by_toilet(self, toilet_id: uuid.UUID, include_deleted: bool = False) -> list[Review]:
        query = (
            select(Review)
            .where(Review.toilet_id == toilet_id)
            .options(selectinload(Review.photos))
        )
        if not include_deleted:
            query = query.where(Review.is_deleted == False)
        query = query.order_by(Review.created_at.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create(self, obj: Review) -> Review:
        self.session.add(obj)
        await self.session.commit()
        result = await self.session.execute(
            select(Review).where(Review.id == obj.id).options(selectinload(Review.photos))
        )
        return result.scalar_one()

    async def soft_delete(
        self,
        review_id: uuid.UUID,
        deleted_by_id: uuid.UUID,
        reason: str,
    ) -> Review | None:
        review = await self.get_by_id(review_id)
        if not review or review.is_deleted:
            return None
        review.is_deleted = True
        review.deleted_reason = reason
        review.deleted_by_id = deleted_by_id
        review.deleted_at = datetime.now(timezone.utc)
        await self.session.commit()
        result = await self.session.execute(
            select(Review).where(Review.id == review_id).options(selectinload(Review.photos))
        )
        return result.scalar_one()
