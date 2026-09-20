"""Вихідні порти для пошуку: сам пошук, кеш і журнал запитів."""

from abc import ABC, abstractmethod

from query_service.domain.search import SearchHit, SearchLogEntry


class RecipeSearchRepository(ABC):
    """Повнотекстовий пошук (реалізація: ElasticRecipeSearchRepository)."""

    @abstractmethod
    async def search(
        self, text: str, cuisine: str | None, max_cook_time_min: int | None, size: int
    ) -> list[SearchHit]: ...


class SearchCachePort(ABC):
    """Кеш результатів пошуку (реалізація: RedisSearchCache)."""

    @abstractmethod
    async def get(self, key: str) -> list[SearchHit] | None:
        """None — промах кешу; порожній список — у кеші збережено «нічого не знайдено»."""

    @abstractmethod
    async def put(self, key: str, hits: list[SearchHit], ttl_sec: int) -> None: ...


class SearchLogRepository(ABC):
    """Журнал останніх запитів (реалізація: RedisSearchLogRepository)."""

    @abstractmethod
    async def append(self, entry: SearchLogEntry) -> None: ...

    @abstractmethod
    async def recent(self, limit: int) -> list[SearchLogEntry]: ...
