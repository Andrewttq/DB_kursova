"""Прикладні сервіси пошуку."""

import hashlib
import json
import logging
import re

from query_service.application.ports.outbound.search_ports import (
    RecipeSearchRepository,
    SearchCachePort,
    SearchLogRepository,
)
from query_service.domain.search import SearchHit, SearchLogEntry

logger = logging.getLogger(__name__)

# Усе, що не буква, не цифра і не пробіл, — розділовий знак.
_NON_WORD = re.compile(r"[^\w\s]", re.UNICODE)


def _light_stem(word: str) -> str:
    """Найпростіший стемінг для англійської множини: chickens -> chicken.

    Elasticsearch з аналізатором english і так шукає «chicken» і «chickens» однаково,
    тож об'єднання цих запитів в один ключ кешу не змінює результат, а лише додає
    попадань у кеш. Короткі слова (gas, egg) і слова на -ss (bass) не чіпаємо.
    """
    if len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
        return word[:-1]
    return word


class QueryNormalizer:
    """Нормалізація пошукового запиту перед зверненням до кешу.

    Мета: різні за написанням, але однакові за змістом запити мають давати
    один ключ кешу. «Chicken Garlic Pasta» і «pasta, garlic chicken» ->
    "chicken garlic pasta".
    Кроки: нижній регістр -> прибрати розділові знаки -> розбити на слова ->
    стемінг множини -> прибрати дублікати -> відсортувати за алфавітом -> склеїти.
    """

    def normalize(self, query: str) -> str:
        words = _NON_WORD.sub(" ", query.lower()).split()
        return " ".join(sorted({_light_stem(w) for w in words}))

    def cache_key(
        self, query: str, filters: dict[str, str | int | float | None], page: int, size: int
    ) -> str:
        """Ключ кешу: "search:" + sha1 від рядка «слова|фільтри|сторінка|розмір».

        Слова — результат normalize(query); фільтри — json.dumps(filters, sort_keys=True).
        Фільтри, номер сторінки та її розмір входять у ключ, інакше запит «chicken»
        з фільтром italian і той самий запит з фільтром mexican дали б спільний результат.
        sha1 робить ключ однакової довжини, хоч який довгий запит.
        """
        raw = "|".join(
            [self.normalize(query), json.dumps(filters, sort_keys=True), str(page), str(size)]
        )
        return "search:" + hashlib.sha1(raw.encode("utf-8")).hexdigest()


class SearchCacheService:
    """Кеш результатів пошуку в Redis (стратегія cache-aside).

    enabled=False вимикає кеш (SEARCH_CACHE_ENABLED=false у .env): потрібно,
    щоб у нагрузочному тесті виміряти швидкість самого Elasticsearch без кешу.
    Якщо Redis недоступний, пошук працює повз кеш (повільніше), а не падає:
    кеш лише прискорює, без нього відповідь усе одно правильна.
    """

    def __init__(self, cache: SearchCachePort, ttl_sec: int, enabled: bool = True) -> None:
        self._cache = cache
        self._ttl_sec = ttl_sec
        self._enabled = enabled

    async def get(self, key: str) -> list[SearchHit] | None:
        if not self._enabled:
            return None
        try:
            return await self._cache.get(key)
        except Exception as exc:  # noqa: BLE001 — Redis недоступний: працюємо без кешу
            logger.warning("Кеш недоступний, шукаємо напряму в Elasticsearch: %s", exc)
            return None

    async def put(self, key: str, hits: list[SearchHit]) -> None:
        # Порожній список теж кладемо в кеш: «нічого не знайдено» — це теж відповідь.
        if not self._enabled:
            return
        try:
            await self._cache.put(key, hits, self._ttl_sec)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Не вдалося покласти результат у кеш: %s", exc)


class RecipeSearchService:
    """Повнотекстовий пошук в Elasticsearch."""

    def __init__(self, repository: RecipeSearchRepository) -> None:
        self._repository = repository

    async def search(
        self,
        text: str,
        cuisine: str | None,
        max_cook_time_min: int | None,
        max_calories: float | None,
        page: int,
        size: int,
    ) -> list[SearchHit]:
        return await self._repository.search(
            text, cuisine, max_cook_time_min, max_calories, page, size
        )


class SearchLogService:
    """Журнал пошукових запитів для блоку «Останні запити» на UI."""

    def __init__(self, repository: SearchLogRepository) -> None:
        self._repository = repository

    async def log(self, entry: SearchLogEntry) -> None:
        # Журнал — допоміжна функція: його збій не повинен ламати сам пошук.
        try:
            await self._repository.append(entry)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Не вдалося записати запит у журнал: %s", exc)

    async def recent(self, limit: int = 20) -> list[SearchLogEntry]:
        return await self._repository.recent(limit)
