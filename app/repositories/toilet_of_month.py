from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.toilet_of_month import ToiletOfMonth
from app.repositories.base import BaseRepository


class ToiletOfMonthRepository(BaseRepository[ToiletOfMonth]):
    model = ToiletOfMonth

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_year_month(self, year: int, month: int) -> ToiletOfMonth | None:
        result = await self.session.execute(
            select(ToiletOfMonth).where(
                ToiletOfMonth.year == year,
                ToiletOfMonth.month == month,
            )
        )
        return result.scalar_one_or_none()

    async def get_history(self, limit: int = 12) -> list[ToiletOfMonth]:
        """Последние N победителей."""
        result = await self.session.execute(
            select(ToiletOfMonth)
            .order_by(ToiletOfMonth.year.desc(), ToiletOfMonth.month.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
