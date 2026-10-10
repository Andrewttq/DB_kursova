"""Вихідні порти панелі моніторингу."""

from abc import ABC, abstractmethod

from query_service.domain.stats import IngestConfig


class StatsReadRepository(ABC):
    """Лічильники, які пишуть ingest- та writer-service (реалізація: RedisStatsReadRepository)."""

    @abstractmethod
    async def get_counters(self) -> dict[str, int]:
        """Ключі словника: read, published, а також saved:<роль> і failed:<роль>
        для кожної ролі writer-service (mongo, es, neo4j)."""

    @abstractmethod
    async def get_saved_last_second(self) -> int:
        """Скільки документів збережено в MongoDB за останню повну секунду (write RPS)."""


class QueueMetricsPort(ABC):
    """Метрики брокера (реалізація: RabbitQueueMetricsAdapter)."""

    @abstractmethod
    async def get_queue_depths(self) -> dict[str, int]:
        """Назва черги -> кількість повідомлень, що чекають. Росте та черга,
        сховище якої не встигає записувати, тому видно вузьке місце."""


class IngestConfigPort(ABC):
    """Налаштування швидкості (реалізація: RedisIngestConfigRepository).

    query-service ПИШЕ ці налаштування (з UI), ingest-service їх ЧИТАЄ.
    """

    @abstractmethod
    async def get(self) -> IngestConfig: ...

    @abstractmethod
    async def save(self, config: IngestConfig) -> None: ...
