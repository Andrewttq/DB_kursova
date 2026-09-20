"""Вихідні порти панелі моніторингу."""

from abc import ABC, abstractmethod

from query_service.domain.stats import IngestConfig


class StatsReadRepository(ABC):
    """Лічильники, які пишуть ingest- та writer-service (реалізація: RedisStatsReadRepository)."""

    @abstractmethod
    async def get_counters(self) -> dict[str, int]:
        """read_total, published_total, saved_total, failed_total."""

    @abstractmethod
    async def get_saved_last_second(self) -> int:
        """Скільки документів збережено за останню повну секунду (write RPS)."""


class QueueMetricsPort(ABC):
    """Метрики брокера (реалізація: RabbitQueueMetricsAdapter)."""

    @abstractmethod
    async def get_queue_depth(self) -> int:
        """Кількість повідомлень, що чекають у черзі. Росте, коли БД не встигають."""


class IngestConfigPort(ABC):
    """Налаштування швидкості (реалізація: RedisIngestConfigRepository).

    query-service ПИШЕ ці налаштування (з UI), ingest-service їх ЧИТАЄ.
    """

    @abstractmethod
    async def get(self) -> IngestConfig: ...

    @abstractmethod
    async def save(self, config: IngestConfig) -> None: ...
