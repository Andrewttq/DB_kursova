"""Прикладний сервіс аналітики."""

from query_service.application.ports.outbound.analytics_ports import RecipeAnalyticsRepository
from query_service.domain.analytics import AggregationReport


class RecipeAnalyticsService:
    def __init__(self, repository: RecipeAnalyticsRepository) -> None:
        self._repository = repository

    async def cuisine_stats(self, max_cook_time_min: int | None) -> AggregationReport:
        return await self._repository.cuisine_stats(max_cook_time_min)
