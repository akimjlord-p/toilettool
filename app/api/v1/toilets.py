import uuid

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import CurrentUser, DbSession
from app.schemas.toilet import ToiletCard, ToiletCreate, ToiletResponse, ToiletSearchResponse
from app.services.toilet import ToiletService

router = APIRouter(prefix="/toilets", tags=["toilets"])


@router.get("/search", response_model=ToiletSearchResponse)
async def search_toilets(
    q: str = Query(min_length=3, description="Адрес или его часть"),
    session: DbSession = None,
):
    """Поиск туалетов по адресу. Используется перед созданием отзыва."""
    service = ToiletService(session)
    result = await service.find_or_suggest(q)
    return {
        "found": result["found"],
        "needs_creation": result["needs_creation"],
    }


@router.post("", response_model=ToiletResponse, status_code=status.HTTP_201_CREATED)
async def create_toilet(
    body: ToiletCreate,
    user: CurrentUser,
    session: DbSession,
):
    """Создать новый туалет. Доступно любому зарегистрированному пользователю."""
    service = ToiletService(session)
    toilet = await service.create(
        address=body.address,
        created_by=user,
        name=body.name,
        lat=body.lat,
        lon=body.lon,
        yandex_place_id=body.yandex_place_id,
    )
    return toilet


@router.get("/{toilet_id}", response_model=ToiletCard)
async def get_toilet(toilet_id: uuid.UUID, session: DbSession):
    """Карточка туалета с агрегированными оценками."""
    service = ToiletService(session)
    card = await service.get_card(toilet_id)
    if not card:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Туалет не найден")
    return card
