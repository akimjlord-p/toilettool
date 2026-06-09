import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.moderator_review import ModeratorReview
from app.repositories.base import BaseRepository


class ModeratorReviewRepository(BaseRepository[ModeratorReview]):
    model = ModeratorReview

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_moderator_and_toilet(
        self, moderator_id: uuid.UUID, toilet_id: uuid.UUID
    ) -> ModeratorReview | None:
        result = await self.session.execute(
            select(ModeratorReview).where(
                ModeratorReview.moderator_id == moderator_id,
                ModeratorReview.toilet_id == toilet_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_toilet(self, toilet_id: uuid.UUID) -> list[ModeratorReview]:
        result = await self.session.execute(
            select(ModeratorReview)
            .where(ModeratorReview.toilet_id == toilet_id)
            .order_by(ModeratorReview.created_at.desc())
        )
        return list(result.scalars().all())
