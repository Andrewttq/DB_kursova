"""Фасад панелі моніторингу — реалізує два вхідні порти.

MonitoringController -> MonitoringFacade -> StatsService (Redis + RabbitMQ)
                                         -> SearchLogService (Redis, останні запити)
                                         -> GeneratorControlService (Redis, швидкість)
"""

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
        raise NotImplementedError

    async def get_config(self) -> IngestConfigDTO:
        raise NotImplementedError

    async def update_config(self, config: IngestConfigDTO) -> IngestConfigDTO:
        raise NotImplementedError
