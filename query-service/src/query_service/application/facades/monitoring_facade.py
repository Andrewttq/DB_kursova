"""Фасад панелі моніторингу — реалізує два вхідні порти.

MonitoringController -> MonitoringFacade -> StatsService (Redis + RabbitMQ)
                                         -> SearchLogService (Redis, останні запити)
                                         -> GeneratorControlService (Redis, швидкість)
"""

from query_service.application import mappers
from query_service.application.dto import IngestConfigDTO, StatsDTO
from query_service.application.ports.inbound.monitoring_use_cases import (
    GeneratorControlUseCase,
    StatsQueryUseCase,
)
from query_service.application.services.monitoring_services import (
    GeneratorControlService,
    StatsService,
)
from query_service.application.services.search_services import SearchLogService
from query_service.domain.stats import IngestConfig

RECENT_SEARCHES_ON_PANEL = 10


class MonitoringFacade(StatsQueryUseCase, GeneratorControlUseCase):
    def __init__(
        self,
        stats: StatsService,
        search_log: SearchLogService,
        generator: GeneratorControlService,
    ) -> None:
        self._stats = stats
        self._search_log = search_log
        self._generator = generator

    async def get_stats(self) -> StatsDTO:
        snap = await self._stats.snapshot()
        recent = await self._search_log.recent(RECENT_SEARCHES_ON_PANEL)
        return StatsDTO(
            read_total=snap.read_total,
            published_total=snap.published_total,
            saved_total=snap.saved_total,
            failed_total=snap.failed_total,
            write_rps=snap.write_rps,
            queue_depths=snap.queue_depths,
            published_rps=snap.published_rps,
            saved_rps=snap.saved_rps,
            recent_searches=[mappers.log_entry_to_dto(e) for e in recent],
        )

    async def get_config(self) -> IngestConfigDTO:
        config = await self._generator.get()
        return IngestConfigDTO(rate_per_sec=config.rate_per_sec, running=config.running)

    async def update_config(self, config: IngestConfigDTO) -> IngestConfigDTO:
        saved = await self._generator.update(
            IngestConfig(rate_per_sec=config.rate_per_sec, running=config.running)
        )
        return IngestConfigDTO(rate_per_sec=saved.rate_per_sec, running=saved.running)
