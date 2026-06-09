from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import DbSession, ModeratorUser
from app.schemas.top import ToiletOfMonthResponse, TopEntry
from app.services.ai import AIService
from app.services.top import TopService
from app.repositories.toilet import ToiletRepository

router = APIRouter(prefix="/top", tags=["top"])


@router.get("", response_model=list[TopEntry])
async def get_top(
    session: DbSession,
    criterion: str = Query(default="total", description="cleanliness / supplies / smell / equipment / privacy / vibe / total"),
    limit: int = Query(default=10, ge=1, le=50),
):
    """Топ туалетов по критерию за всё время."""
    service = TopService(session)
    try:
        top = await service.get_top(criterion=criterion, limit=limit)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return top


@router.get("/month", response_model=ToiletOfMonthResponse | None)
async def get_toilet_of_month(
    session: DbSession,
    year: int | None = None,
    month: int | None = None,
):
    """Туалет месяца. Без параметров — текущий месяц."""
    service = TopService(session)
    result = await service.get_toilet_of_month(year=year, month=month)
    return result


@router.get("/month/history", response_model=list[ToiletOfMonthResponse])
async def get_month_history(
    session: DbSession,
    limit: int = Query(default=12, ge=1, le=60),
):
    """Архив победителей по месяцам."""
    service = TopService(session)
    return await service.get_history(limit=limit)


@router.post("/month/assign", response_model=ToiletOfMonthResponse)
async def assign_toilet_of_month(
    moderator: ModeratorUser,
    session: DbSession,
    year: int | None = None,
    month: int | None = None,
    generate_ai_comment: bool = True,
):
    """
    Назначить туалет месяца вручную (модератор).
    Опционально генерирует AI-комментарий через GPT-4o.
    """
    service = TopService(session)
    ai_service = AIService()

    try:
        # Сначала определяем победителя без AI-комментария
        record = await service.assign_toilet_of_month(year=year, month=month)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Генерируем AI-комментарий если нужно
    if generate_ai_comment:
        toilet_repo = ToiletRepository(session)
        avg_scores = await toilet_repo.get_avg_scores(record.toilet_id)
        ai_comment = await ai_service.comment_toilet_of_month(
            address=record.toilet.address,
            name=record.toilet.name,
            avg_score=float(record.avg_score),
            month=record.month,
            year=record.year,
            scores=avg_scores or {},
        )
        record.ai_comment = ai_comment
        await session.commit()
        await session.refresh(record)

    return record
