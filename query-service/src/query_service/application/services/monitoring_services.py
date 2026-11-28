"""Прикладні сервіси панелі моніторингу."""

import time
from collections import deque
from collections.abc import Callable

from query_service.application.ports.outbound.monitoring_ports import (
    IngestConfigPort,
    QueueMetricsPort,
    StatsReadRepository,
)
from query_service.domain.stats import IngestConfig, SystemStats

MIN_RATE = 10
MAX_RATE = 5000
WRITER_ROLES = ("mongo", "es", "neo4j")
# Швидкість рахуємо за кілька секунд, щоб цифра не стрибала від пачки до пачки.
RATE_WINDOW_SEC = 5.0


class StatsService:
    """Збирає статистику з кількох джерел в один знімок.

    Вимога методички: швидкість запису на UI має братися зі звернення до БД,
    а не з пам'яті процесу. Тому все читається з Redis і RabbitMQ.
    """

    def __init__(
        self,
        stats: StatsReadRepository,
        queue: QueueMetricsPort,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._stats = stats
        self._queue = queue
        self._clock = clock
        # Попередні знімки лічильників: (час, опубліковано, збережено за сховищами).
        # Самі лічильники — у Redis; тут лише кілька точок, щоб порахувати різницю за час.
        self._history: deque[tuple[float, int, dict[str, int]]] = deque()

    async def snapshot(self) -> SystemStats:
        counters = await self._stats.get_counters()
        published = counters.get("published", 0)
        saved = {r: counters.get(f"saved:{r}", 0) for r in WRITER_ROLES}
        published_rps, saved_rps = self._rates(published, saved)
        return SystemStats(
            read_total=counters.get("read", 0),
            published_total=published,
            saved_total=saved,
            failed_total=sum(counters.get(f"failed:{r}", 0) for r in WRITER_ROLES),
            write_rps=float(await self._stats.get_saved_last_second()),
            queue_depths=await self._queue.get_queue_depths(),
            published_rps=published_rps,
            saved_rps=saved_rps,
        )

    def _rates(self, published: int, saved: dict[str, int]) -> tuple[float, dict[str, float]]:
        """Записів/с = (лічильник зараз - лічильник ~5 с тому) / минулий час."""
        now = self._clock()
        self._history.append((now, published, saved))
        while len(self._history) > 2 and now - self._history[1][0] >= RATE_WINDOW_SEC:
            self._history.popleft()
        then, old_published, old_saved = self._history[0]
        elapsed = now - then
        if elapsed <= 0:
            return 0.0, {r: 0.0 for r in WRITER_ROLES}
        # max(0, ...) — якщо лічильники в Redis скинули, швидкість не стає від'ємною
        return (
            max(0.0, (published - old_published) / elapsed),
            {r: max(0.0, (saved[r] - old_saved.get(r, 0)) / elapsed) for r in WRITER_ROLES},
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
