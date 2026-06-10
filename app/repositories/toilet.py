from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

# ~200 метров в градусах (приближение для широт 50-60°)
GEO_RADIUS_LAT = 0.002
GEO_RADIUS_LON = 0.003

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

    async def search_by_coords(self, lat: float, lon: float, limit: int = 5) -> list[Toilet]:
        """
        Ищет туалеты в радиусе ~200м по координатам.
        Использует bounding box — быстро без PostGIS.
        """
        result = await self.session.execute(
            select(Toilet)
            .where(
                and_(
                    Toilet.lat.isnot(None),
                    Toilet.lon.isnot(None),
                    Toilet.lat.between(lat - GEO_RADIUS_LAT, lat + GEO_RADIUS_LAT),
                    Toilet.lon.between(lon - GEO_RADIUS_LON, lon + GEO_RADIUS_LON),
                )
            )
            .limit(limit)
        )
        return list(result.scalars().all())

    async def search_combined(self, query: str, lat: float | None = None, lon: float | None = None, limit: int = 5) -> list[Toilet]:
        """
        Сначала ищет по координатам (если есть), потом по тексту.
        Объединяет результаты без дублей.
        """
        results: list[Toilet] = []
        seen_ids: set = set()

        if lat and lon:
            by_coords = await self.search_by_coords(lat, lon, limit)
            for t in by_coords:
                if t.id not in seen_ids:
                    results.append(t)
                    seen_ids.add(t.id)

        if len(results) < limit:
            by_text = await self.search_by_address(query, limit)
            for t in by_text:
                if t.id not in seen_ids:
                    results.append(t)
                    seen_ids.add(t.id)

        return results[:limit]

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
