"""Вихідний адаптер Redis для лічильників запису."""

from redis.asyncio import Redis

from writer_service.application.ports.outbound.stats_repositories import WriteStatsRepository


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
        raise NotImplementedError

    async def incr_failed(self, count: int) -> None:
        raise NotImplementedError
