import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.toilet import Toilet
from app.models.user import User
from app.repositories.toilet import ToiletRepository


class ToiletService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = ToiletRepository(session)

    async def search_by_address(self, query: str) -> list[Toilet]:
        """
        Поиск туалетов по адресу.
        Используется когда юзер вводит адрес — показываем ему кандидатов.
        """
        if len(query.strip()) < 3:
            return []
        return await self.repo.search_by_address(query)

    async def get_by_id(self, toilet_id: uuid.UUID) -> Toilet | None:
        return await self.repo.get_by_id(toilet_id)

    async def create(
        self,
        address: str,
        created_by: User,
        name: str | None = None,
        lat: float | None = None,
        lon: float | None = None,
        yandex_place_id: str | None = None,
    ) -> Toilet:
        """
        Создать новый туалет.
        Любой зарегистрированный юзер может добавить туалет.
        """
        toilet = Toilet(
            address=address,
            name=name,
            lat=lat,
            lon=lon,
            yandex_place_id=yandex_place_id,
            created_by_id=created_by.id,
        )
        return await self.repo.create(toilet)

    async def get_card(self, toilet_id: uuid.UUID) -> dict | None:
        """
        Карточка туалета — данные + агрегированные оценки.
        Возвращает None если туалет не найден.
        """
        toilet = await self.repo.get_by_id(toilet_id)
        if not toilet:
            return None

        avg_scores = await self.repo.get_avg_scores(toilet_id)

        return {
            "toilet": toilet,
            "avg_scores": avg_scores,  # None если отзывов ещё нет
        }

    async def find_or_suggest(self, address: str) -> dict:
        """
        Основной флоу при оценке:
        1. Ищем туалеты по адресу
        2. Если нашли — предлагаем выбрать
        3. Если нет — сигнализируем что нужно создать новый

        Возвращает:
        {
            "found": [Toilet, ...],   # список кандидатов (может быть пустым)
            "needs_creation": bool    # True если ничего не нашли
        }
        """
        found = await self.search_by_address(address)
        return {
            "found": found,
            "needs_creation": len(found) == 0,
        }
