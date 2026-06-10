import aiohttp


class GeocoderResult:
    def __init__(self, address: str, lat: float, lon: float, yandex_place_id: str | None = None):
        self.address = address
        self.lat = lat
        self.lon = lon
        self.yandex_place_id = yandex_place_id


class YandexGeocoder:
    BASE_URL = "https://geocode-maps.yandex.ru/1.x/"

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def geocode(self, address: str) -> GeocoderResult | None:
        """
        Нормализует адрес и возвращает координаты.
        Возвращает None если адрес не найден или ключ не задан.
        """
        if not self.api_key:
            return None

        params = {
            "apikey": self.api_key,
            "geocode": address,
            "format": "json",
            "results": 1,
            "lang": "ru_RU",
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.BASE_URL, params=params, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    if resp.status != 200:
                        return None
                    data = await resp.json()
        except Exception:
            return None

        try:
            collection = data["response"]["GeoObjectCollection"]
            members = collection["featureMember"]
            if not members:
                return None

            obj = members[0]["GeoObject"]
            pos = obj["Point"]["pos"]  # "lon lat"
            lon, lat = map(float, pos.split())

            # Нормализованный адрес
            normalized = obj["metaDataProperty"]["GeocoderMetaData"]["text"]
            place_id = obj.get("uri", "")

            return GeocoderResult(
                address=normalized,
                lat=lat,
                lon=lon,
                yandex_place_id=place_id or None,
            )
        except (KeyError, IndexError, ValueError):
            return None
