"""Прикладні сервіси пошуку."""

from query_service.application.ports.outbound.search_ports import (
    RecipeSearchRepository,
    SearchCachePort,
    SearchLogRepository,
)
from query_service.domain.search import SearchHit, SearchLogEntry


class QueryNormalizer:
    """Нормалізація пошукового запиту перед зверненням до кешу.

    Мета: різні за написанням, але однакові за змістом запити мають давати
    один ключ кешу. «Chicken Garlic Pasta» і «pasta, garlic chicken» ->
    "search:chicken garlic pasta|*|*".
    Кроки: нижній регістр -> прибрати розділові знаки -> розбити на слова ->
    прибрати дублікати -> відсортувати за алфавітом -> склеїти.
    Стемінг (прибирання закінчень) — бонус, робиться пізніше.
    """

    def normalize(self, query: str) -> str:
        raise NotImplementedError

    def cache_key(self, query: str, cuisine: str | None, max_cook_time_min: int | None) -> str:
        """Ключ включає і фільтри, інакше пошук з різними фільтрами дасть однаковий кеш."""
        raise NotImplementedError


class SearchCacheService:
    """Кеш результатів пошуку в Redis (стратегія cache-aside)."""

    def __init__(self, cache: SearchCachePort, ttl_sec: int) -> None:
        self._cache = cache
        self._ttl_sec = ttl_sec

    async def get(self, key: str) -> list[SearchHit] | None:
        raise NotImplementedError

    async def put(self, key: str, hits: list[SearchHit]) -> None:
        raise NotImplementedError


class RecipeSearchService:
    """Повнотекстовий пошук в Elasticsearch."""

    def __init__(self, repository: RecipeSearchRepository) -> None:
        self._repository = repository

    async def search(
        self, text: str, cuisine: str | None, max_cook_time_min: int | None, size: int
    ) -> list[SearchHit]:
        raise NotImplementedError


class SearchLogService:
    """Журнал пошукових запитів для блоку «Останні запити» на UI."""

    def __init__(self, repository: SearchLogRepository) -> None:
        self._repository = repository

    async def log(self, entry: SearchLogEntry) -> None:
        raise NotImplementedError

    async def recent(self, limit: int = 20) -> list[SearchLogEntry]:
        raise NotImplementedError
