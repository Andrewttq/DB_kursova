"""Вихідний адаптер — читання налаштувань швидкості з Redis."""

from redis.asyncio import Redis

from ingest_service.application.ports.outbound.ingest_config_port import IngestConfigPort

KEY = "ingest:config"
MIN_RATE, MAX_RATE = 10, 5000


class RedisIngestConfigRepository(IngestConfigPort):
    """Реалізує IngestConfigPort.

    Налаштування зберігаються в хеші Redis `ingest:config`
    з полями `rate` і `running`. Записує їх query-service (слайдер на UI).
    Якщо ключа ще немає — повертаються значення за замовчуванням.
    """

    def __init__(self, redis_url: str, default_rate: int) -> None:
        # Клієнт не відкриває з'єднання одразу, лише при першій команді.
        self._redis = Redis.from_url(redis_url)
        self._default_rate = default_rate

    async def get_rate(self) -> int:
        value = await self._redis.hget(KEY, "rate")
        rate = int(value) if value is not None else self._default_rate
        return max(MIN_RATE, min(MAX_RATE, rate))  # захист від некоректного значення

    async def is_running(self) -> bool:
        value = await self._redis.hget(KEY, "running")
        return value != b"0"  # ключа немає -> працюємо за замовчуванням

    async def close(self) -> None:
        await self._redis.aclose()
