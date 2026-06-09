from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.review import Review
from app.models.toilet import Toilet
from app.repositories.base import BaseRepository

SCORE_COLUMNS = {
    "cleanliness": Review.score_cleanliness,
    "supplies": Review.score_supplies,
    "smell": Review.score_smell,
    "equipment": Review.score_equipment,
    "privacy": Review.score_privacy,
    "vibe": Review.score_vibe,
    "total": Review.total_score,
}


class ToiletRepository(BaseRepository[Toilet]):
    model = Toilet

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def search_by_address(self, query: str, limit: int = 5) -> list[Toilet]:
        """Ищет туалеты по частичному совпадению адреса (case-insensitive)."""
        result = await self.session.execute(
            select(Toilet)
            .where(Toilet.address.ilike(f"%{query}%"))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_avg_scores(self, toilet_id) -> dict | None:
        """Возвращает средние оценки по всем критериям для туалета."""
        result = await self.session.execute(
            select(
                func.avg(Review.score_cleanliness).label("cleanliness"),
                func.avg(Review.score_supplies).label("supplies"),
                func.avg(Review.score_smell).label("smell"),
                func.avg(Review.score_equipment).label("equipment"),
                func.avg(Review.score_privacy).label("privacy"),
                func.avg(Review.score_vibe).label("vibe"),
                func.avg(Review.total_score).label("total"),
                func.count(Review.id).label("review_count"),
            )
            .where(Review.toilet_id == toilet_id, Review.is_deleted == False)
        )
        row = result.one_or_none()
        if not row or row.review_count == 0:
            return None
        return {
            "cleanliness": round(float(row.cleanliness), 2) if row.cleanliness else 0,
            "supplies": round(float(row.supplies), 2) if row.supplies else 0,
            "smell": round(float(row.smell), 2) if row.smell else 0,
            "equipment": round(float(row.equipment), 2) if row.equipment else 0,
            "privacy": round(float(row.privacy), 2) if row.privacy else 0,
            "vibe": round(float(row.vibe), 2) if row.vibe else 0,
            "total": round(float(row.total), 2) if row.total else 0,
            "review_count": row.review_count,
        }

    async def get_top(self, criterion: str = "total", limit: int = 10) -> list[dict]:
        """Топ туалетов по выбранному критерию."""
        score_col = SCORE_COLUMNS.get(criterion, Review.total_score)
        result = await self.session.execute(
            select(
                Toilet,
                func.avg(score_col).label("avg_score"),
                func.count(Review.id).label("review_count"),
            )
            .join(Review, Review.toilet_id == Toilet.id)
            .where(Review.is_deleted == False)
            .group_by(Toilet.id)
            .order_by(func.avg(score_col).desc())
            .limit(limit)
        )
        return [
            {"toilet": row.Toilet, "avg_score": round(float(row.avg_score), 2), "review_count": row.review_count}
            for row in result.all()
        ]

    async def get_top_for_period(self, year: int, month: int, limit: int = 10) -> list[dict]:
        """Топ туалетов за конкретный месяц (для туалета месяца)."""
        from sqlalchemy import extract
        result = await self.session.execute(
            select(
                Toilet,
                func.avg(Review.total_score).label("avg_score"),
                func.count(Review.id).label("review_count"),
            )
            .join(Review, Review.toilet_id == Toilet.id)
            .where(
                Review.is_deleted == False,
                extract("year", Review.created_at) == year,
                extract("month", Review.created_at) == month,
            )
            .group_by(Toilet.id)
            .order_by(func.avg(Review.total_score).desc())
            .limit(limit)
        )
        return [
            {"toilet": row.Toilet, "avg_score": round(float(row.avg_score), 2), "review_count": row.review_count}
            for row in result.all()
        ]
