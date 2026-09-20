"""Вихідні адаптери Redis: кеш пошуку, журнал запитів, статистика, налаштування швидкості."""

from redis.asyncio import Redis

from query_service.application.ports.outbound.monitoring_ports import (
    IngestConfigPort,
    StatsReadRepository,
)
from query_service.application.ports.outbound.search_ports import (
    SearchCachePort,
    SearchLogRepository,
)
from query_service.domain.search import SearchHit, SearchLogEntry
from query_service.domain.stats import IngestConfig


class RedisSearchCache(SearchCachePort):
    """Кеш результатів: ключ з QueryNormalizer, значення — JSON зі списком SearchHit.

    Команда SET key value EX ttl — Redis сам видалить запис після закінчення TTL.
    """

    def __init__(self, client: Redis) -> None:
        self._client = client

    async def get(self, key: str) -> list[SearchHit] | None:
        raise NotImplementedError

    async def put(self, key: str, hits: list[SearchHit], ttl_sec: int) -> None:
        raise NotImplementedError


class RedisSearchLogRepository(SearchLogRepository):
    """Журнал: список `search:log`, LPUSH нового запису + LTRIM до 50 останніх."""

    def __init__(self, client: Redis) -> None:
        self._client = client

    async def append(self, entry: SearchLogEntry) -> None:
        raise NotImplementedError

    async def recent(self, limit: int) -> list[SearchLogEntry]:
        raise NotImplementedError


class RedisStatsReadRepository(StatsReadRepository):
    """Читає лічильники stats:*, які записують ingest- та writer-service."""

    def __init__(self, client: Redis) -> None:
        self._client = client

    async def get_counters(self) -> dict[str, int]:
        raise NotImplementedError

    async def get_saved_last_second(self) -> int:
        """Ключ stats:saved:<попередня unix-секунда>."""
        raise NotImplementedError


class RedisIngestConfigRepository(IngestConfigPort):
    """Хеш `ingest:config` з полями rate і running (читає ingest-service)."""

    def __init__(self, client: Redis) -> None:
        self._client = client

    async def get(self) -> IngestConfig:
        raise NotImplementedError

    async def save(self, config: IngestConfig) -> None:
        raise NotImplementedError
