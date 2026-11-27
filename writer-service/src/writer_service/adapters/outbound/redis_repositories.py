"""Вихідний адаптер Redis для лічильників запису."""

import time

from redis.asyncio import Redis

from writer_service.application.ports.outbound.stats_repositories import WriteStatsRepository

PER_SECOND_TTL = 60


class RedisWriteStatsRepository(WriteStatsRepository):
    """Реалізує WriteStatsRepository.

    Кожен екземпляр writer-service веде лічильники своєї ролі (mongo, es або neo4j),
    бо три екземпляри пишуть у сховища незалежно один від одного. Ключі:
        stats:saved:<роль>                — загальна кількість збережених
                                            (stats:saved:mongo, stats:saved:es, stats:saved:neo4j);
        stats:saved:<роль>:<unix-секунда> — збережені за конкретну секунду (TTL 60 с),
                                            з них query-service рахує write RPS;
        stats:failed:<роль>               — пачки, які не вдалося записати.
    Усі збільшення — атомарним INCRBY в одному pipeline.
    """

    def __init__(self, client: Redis, role: str) -> None:
        self._client = client
        self._role = role

    async def incr_saved(self, count: int) -> None:
        if count <= 0:
            return
        second_key = f"stats:saved:{self._role}:{int(time.time())}"
        async with self._client.pipeline(transaction=True) as pipe:
            pipe.incrby(f"stats:saved:{self._role}", count)
            pipe.incrby(second_key, count)
            pipe.expire(second_key, PER_SECOND_TTL)
            await pipe.execute()

    async def incr_failed(self, count: int) -> None:
        await self._client.incrby(f"stats:failed:{self._role}", count)
