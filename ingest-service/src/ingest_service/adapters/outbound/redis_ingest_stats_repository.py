"""Вихідний адаптер — лічильники ingest-service у Redis."""

from ingest_service.application.ports.outbound.ingest_stats_port import IngestStatsPort


class RedisIngestStatsRepository(IngestStatsPort):
    """Реалізує IngestStatsPort через атомарну команду INCRBY.

    Ключі: `stats:read_total`, `stats:published_total`.
    Атомарність важлива: якщо запустити кілька екземплярів сервісу,
    лічильник не «загубить» збільшення.
    """

    def __init__(self, redis_url: str) -> None:
        self._redis_url = redis_url

    async def incr_read(self, count: int) -> None:
        raise NotImplementedError

    async def incr_published(self, count: int) -> None:
        raise NotImplementedError
