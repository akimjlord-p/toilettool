import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.toilet import Toilet
from app.models.user import User
from app.repositories.toilet import ToiletRepository
from app.services.geocoder import YandexGeocoder


def _get_geocoder() -> YandexGeocoder:
    return YandexGeocoder(api_key=settings.yandex_geocoder_key)


class ToiletService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = ToiletRepository(session)
        self.geocoder = _get_geocoder()

    async def search_by_address(self, query: str) -> list[Toilet]:
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
        Создать туалет.
        Если координаты не переданы — пробуем геокодировать адрес.
        """
        final_address = address
        final_lat = lat
        final_lon = lon
        final_place_id = yandex_place_id

        if not lat or not lon:
            geo = await self.geocoder.geocode(address)
            if geo:
                final_address = geo.address
                final_lat = geo.lat
                final_lon = geo.lon
                final_place_id = geo.yandex_place_id

        toilet = Toilet(
            address=final_address,
            name=name,
            lat=final_lat,
            lon=final_lon,
            yandex_place_id=final_place_id,
            created_by_id=created_by.id,
        )
        return await self.repo.create(toilet)

    async def get_card(self, toilet_id: uuid.UUID) -> dict | None:
        toilet = await self.repo.get_by_id(toilet_id)
        if not toilet:
            return None
        avg_scores = await self.repo.get_avg_scores(toilet_id)
        return {"toilet": toilet, "avg_scores": avg_scores}

    async def find_or_suggest(self, address: str) -> dict:
        """
        Главный флоу поиска:
        1. Геокодируем адрес → получаем координаты
        2. Ищем по координатам (точно) + по тексту (fallback)
        3. Если ничего нет → нужно создавать новый
        """
        if len(address.strip()) < 3:
            return {"found": [], "needs_creation": True, "normalized_address": address, "lat": None, "lon": None}

        lat = lon = None
        normalized_address = address

        geo = await self.geocoder.geocode(address)
        if geo:
            lat = geo.lat
            lon = geo.lon
            normalized_address = geo.address

        found = await self.repo.search_combined(query=address, lat=lat, lon=lon)

        return {
            "found": found,
            "needs_creation": len(found) == 0,
            "normalized_address": normalized_address,
            "lat": lat,
            "lon": lon,
        }
