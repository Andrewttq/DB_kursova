"""Прикладний сервіс — бізнес-логіка ingest-service.

Реалізує вхідний порт IngestUseCase і використовує лише вихідні порти (інтерфейси).
Зверніть увагу: тут немає жодного імпорту aio_pika, redis чи csv. Конкретні
реалізації портів передаються в конструктор ззовні (див. container.py) —
це і є впровадження залежностей (Dependency Injection).
"""

import logging

from ingest_service.application.ports.inbound.ingest_use_case import IngestUseCase
from ingest_service.application.ports.outbound.ingest_config_port import IngestConfigPort
from ingest_service.application.ports.outbound.ingest_stats_port import IngestStatsPort
from ingest_service.application.ports.outbound.recipe_publisher_port import RecipePublisherPort
from ingest_service.application.ports.outbound.recipe_source_port import RecipeSourcePort
from ingest_service.application.services.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


class IngestService(IngestUseCase):
    def __init__(
        self,
        source: RecipeSourcePort,
        publisher: RecipePublisherPort,
        config: IngestConfigPort,
        stats: IngestStatsPort,
        rate_limiter: RateLimiter,
    ) -> None:
        self._source = source
        self._publisher = publisher
        self._config = config
        self._stats = stats
        self._rate_limiter = rate_limiter

    async def run_tick(self) -> int:
        """Один такт:
        1. config.is_running() — якщо вимкнено, нічого не робити;
        2. config.get_rate() -> rate_limiter.batch_size(rate);
        3. source.next_batch(size) -> stats.incr_read(...);
        4. publisher.publish_batch(batch) -> stats.incr_published(...).
        """
        if not await self._config.is_running():
            self._rate_limiter.reset()
            return 0
        size = self._rate_limiter.batch_size(await self._config.get_rate())
        if size == 0:
            return 0  # при малій швидкості маркери накопичуються кілька тактів

        batch = await self._source.next_batch(size)
        if not batch:
            return 0
        await self._stats.incr_read(len(batch))

        published = await self._publisher.publish_batch(batch)
        await self._stats.incr_published(published)
        logger.debug("Такт: прочитано %d, опубліковано %d", len(batch), published)
        return published
