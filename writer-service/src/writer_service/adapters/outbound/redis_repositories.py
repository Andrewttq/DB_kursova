"""Вихідний адаптер Redis для лічильників запису."""

from redis.asyncio import Redis

from writer_service.application.ports.outbound.stats_repositories import WriteStatsRepository


class RedisWriteStatsRepository(WriteStatsRepository):
    """Реалізує WriteStatsRepository.

    Ключі:
        stats:saved_total          — загальна кількість збережених;
        stats:saved:<unix-секунда> — збережені за конкретну секунду (TTL 60 с),
                                     з них query-service рахує write RPS;
        stats:failed_total.
    Усі збільшення — атомарним INCRBY в одному pipeline.
    """

    def __init__(self, client: Redis) -> None:
        self._client = client

    async def incr_saved(self, count: int) -> None:
        raise NotImplementedError

    async def incr_failed(self, count: int) -> None:
        raise NotImplementedError
