from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.toilet_of_month import ToiletOfMonth
from app.repositories.toilet import ToiletRepository
from app.repositories.toilet_of_month import ToiletOfMonthRepository

VALID_CRITERIA = {"cleanliness", "supplies", "smell", "equipment", "privacy", "vibe", "total"}


class TopService:
    def __init__(self, session: AsyncSession) -> None:
        self.toilet_repo = ToiletRepository(session)
        self.tom_repo = ToiletOfMonthRepository(session)

    async def get_top(self, criterion: str = "total", limit: int = 10) -> list[dict]:
        """
        Топ туалетов по критерию за всё время.
        criterion — одно из: cleanliness, supplies, smell, equipment, privacy, vibe, total
        """
        if criterion not in VALID_CRITERIA:
            raise ValueError(f"Неизвестный критерий: {criterion}. Доступные: {VALID_CRITERIA}")

        return await self.toilet_repo.get_top(criterion=criterion, limit=limit)

    async def get_toilet_of_month(self, year: int | None = None, month: int | None = None) -> ToiletOfMonth | None:
        """
        Получить туалет месяца.
        Если год/месяц не указаны — берём текущий.
        """
        today = date.today()
        year = year or today.year
        month = month or today.month

        return await self.tom_repo.get_by_year_month(year, month)

    async def assign_toilet_of_month(
        self,
        year: int | None = None,
        month: int | None = None,
        ai_comment: str | None = None,
    ) -> ToiletOfMonth:
        """
        Назначить туалет месяца — берёт победителя за период и сохраняет в историю.
        Вызывается вручную модератором или автоматически по расписанию.
        """
        today = date.today()
        year = year or today.year
        month = month or today.month

        # Проверяем — может уже назначен
        existing = await self.tom_repo.get_by_year_month(year, month)
        if existing:
            raise ValueError(f"Туалет месяца за {month}/{year} уже назначен")

        # Берём топ-1 за этот месяц
        top = await self.toilet_repo.get_top_for_period(year=year, month=month, limit=1)
        if not top:
            raise ValueError(f"За {month}/{year} нет ни одного отзыва — не из чего выбирать")

        winner = top[0]

        record = ToiletOfMonth(
            toilet_id=winner["toilet"].id,
            year=year,
            month=month,
            avg_score=winner["avg_score"],
            ai_comment=ai_comment,
        )
        return await self.tom_repo.create(record)

    async def get_history(self, limit: int = 12) -> list[ToiletOfMonth]:
        """Архив победителей за последние N месяцев."""
        return await self.tom_repo.get_history(limit=limit)
