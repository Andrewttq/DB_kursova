"""Прикладні сервіси панелі моніторингу."""

from query_service.application.ports.outbound.monitoring_ports import (
    IngestConfigPort,
    QueueMetricsPort,
    StatsReadRepository,
)
from query_service.domain.stats import IngestConfig, SystemStats


class StatsService:
    """Збирає статистику з кількох джерел в один знімок.

    Вимога методички: швидкість запису на UI має братися зі звернення до БД,
    а не з пам'яті процесу. Тому все читається з Redis і RabbitMQ.
    """

    def __init__(self, stats: StatsReadRepository, queue: QueueMetricsPort) -> None:
        self._stats = stats
        self._queue = queue

    async def snapshot(self) -> SystemStats:
        raise NotImplementedError


class GeneratorControlService:
    """Читання та зміна швидкості завантаження."""

    def __init__(self, config: IngestConfigPort, default_rate: int) -> None:
        self._config = config
        self._default_rate = default_rate

    async def get(self) -> IngestConfig:
        raise NotImplementedError

    async def update(self, config: IngestConfig) -> IngestConfig:
        """Обмежити швидкість межами 10..5000 і зберегти."""
        raise NotImplementedError
