"""Вихідні адаптери Redis: кеш пошуку, журнал запитів, статистика, налаштування швидкості.

Клієнт Redis створено без decode_responses, тому значення приходять байтами:
json.loads і int() приймають bytes напряму, рядки декодуємо через .decode().
"""

import json
import time
from dataclasses import asdict
from datetime import datetime

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

SEARCH_LOG_KEY = "search:log"
SEARCH_LOG_MAX = 100
WRITER_ROLES = ("mongo", "es", "neo4j")


# ---------------------------------------------------------------- пошук (зона C)


class RedisSearchCache(SearchCachePort):
    """Кеш результатів: ключ з QueryNormalizer, значення — JSON зі списком SearchHit.

    Команда SET key value EX ttl — Redis сам видалить запис після закінчення TTL.
    """

    def __init__(self, client: Redis) -> None:
        self._client = client

    async def get(self, key: str) -> list[SearchHit] | None:
        raw = await self._client.get(key)
        if raw is None:
            return None  # промах кешу
        return [SearchHit(**item) for item in json.loads(raw)]

    async def put(self, key: str, hits: list[SearchHit], ttl_sec: int) -> None:
        await self._client.set(key, json.dumps([asdict(h) for h in hits]), ex=ttl_sec)


class RedisSearchLogRepository(SearchLogRepository):
    """Журнал: список `search:log`, LPUSH нового запису + LTRIM до 100 останніх."""

    def __init__(self, client: Redis) -> None:
        self._client = client

    async def append(self, entry: SearchLogEntry) -> None:
        data = asdict(entry)
        data["timestamp"] = entry.timestamp.isoformat()  # datetime не серіалізується в JSON
        # pipeline відправляє обидві команди одним мережевим зверненням
        async with self._client.pipeline(transaction=False) as pipe:
            pipe.lpush(SEARCH_LOG_KEY, json.dumps(data, ensure_ascii=False))
            pipe.ltrim(SEARCH_LOG_KEY, 0, SEARCH_LOG_MAX - 1)
            await pipe.execute()

    async def recent(self, limit: int) -> list[SearchLogEntry]:
        items = await self._client.lrange(SEARCH_LOG_KEY, 0, limit - 1)
        result = []
        for raw in items:
            data = json.loads(raw)
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
            result.append(SearchLogEntry(**data))
        return result


# ---------------------------------------------------------- моніторинг (зона A)


class RedisStatsReadRepository(StatsReadRepository):
    """Читає лічильники stats:*, які записують ingest- та writer-service.

    Ключі: stats:read, stats:published (ingest-service);
    stats:saved:<роль>, stats:failed:<роль> для ролей mongo, es, neo4j
    (кожен екземпляр writer-service веде власні лічильники).
    Усі ключі читаються однією командою MGET.
    """

    def __init__(self, client: Redis) -> None:
        self._client = client

    async def get_counters(self) -> dict[str, int]:
        names = ["read", "published"]
        names += [f"saved:{r}" for r in WRITER_ROLES]
        names += [f"failed:{r}" for r in WRITER_ROLES]
        values = await self._client.mget([f"stats:{n}" for n in names])
        return {name: int(value or 0) for name, value in zip(names, values, strict=True)}

    async def get_saved_last_second(self) -> int:
        """Ключ stats:saved:mongo:<попередня unix-секунда>.

        Беремо саме попередню секунду: поточна ще не закінчилася і лічильник неповний.
        """
        value = await self._client.get(f"stats:saved:mongo:{int(time.time()) - 1}")
        return int(value or 0)


class RedisIngestConfigRepository(IngestConfigPort):
    """Хеш `ingest:config` з полями rate і running (читає ingest-service)."""

    KEY = "ingest:config"

    def __init__(self, client: Redis, default_rate: int = 10) -> None:
        self._client = client
        self._default_rate = default_rate

    async def get(self) -> IngestConfig:
        data = await self._client.hgetall(self.KEY)
        rate = int(data.get(b"rate", self._default_rate))
        running = data.get(b"running", b"1") != b"0"
        return IngestConfig(rate_per_sec=rate, running=running)

    async def save(self, config: IngestConfig) -> None:
        await self._client.hset(
            self.KEY,
            mapping={"rate": config.rate_per_sec, "running": "1" if config.running else "0"},
        )
