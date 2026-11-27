"""Прикладні сервіси панелі моніторингу."""

from query_service.application.ports.outbound.monitoring_ports import (
    IngestConfigPort,
    QueueMetricsPort,
    StatsReadRepository,
)
from query_service.domain.stats import IngestConfig, SystemStats

MIN_RATE = 10
MAX_RATE = 5000
WRITER_ROLES = ("mongo", "es", "neo4j")


class StatsService:
    """Збирає статистику з кількох джерел в один знімок.

    Вимога методички: швидкість запису на UI має братися зі звернення до БД,
    а не з пам'яті процесу. Тому все читається з Redis і RabbitMQ.
    """

    def __init__(self, stats: StatsReadRepository, queue: QueueMetricsPort) -> None:
        self._stats = stats
        self._queue = queue

    async def snapshot(self) -> SystemStats:
        counters = await self._stats.get_counters()
        return SystemStats(
            read_total=counters.get("read", 0),
            published_total=counters.get("published", 0),
            saved_total={r: counters.get(f"saved:{r}", 0) for r in WRITER_ROLES},
            failed_total=sum(counters.get(f"failed:{r}", 0) for r in WRITER_ROLES),
            write_rps=float(await self._stats.get_saved_last_second()),
            queue_depths=await self._queue.get_queue_depths(),
        )


class GeneratorControlService:
    """Читання та зміна швидкості завантаження."""

    def __init__(self, config: IngestConfigPort, default_rate: int) -> None:
        self._config = config
        self._default_rate = default_rate

    async def get(self) -> IngestConfig:
        return await self._config.get()

    async def update(self, config: IngestConfig) -> IngestConfig:
        """Обмежити швидкість межами 10..5000 і зберегти."""
        clamped = IngestConfig(
            rate_per_sec=max(MIN_RATE, min(MAX_RATE, config.rate_per_sec)),
            running=config.running,
        )
        await self._config.save(clamped)
        return clamped
