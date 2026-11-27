"""Фасад — реалізація RecipeAnalyticsUseCase.

AnalyticsController -> AnalyticsFacade -> RecipeAnalyticsService
                    -> MongoRecipeAnalyticsRepository -> mongos -> shard1, shard2, shard3
"""

from dataclasses import asdict

from query_service.application.dto import AggregationReportDTO
from query_service.application.ports.inbound.analytics_use_case import RecipeAnalyticsUseCase
from query_service.application.services.analytics_service import RecipeAnalyticsService


class AnalyticsFacade(RecipeAnalyticsUseCase):
    def __init__(self, analytics: RecipeAnalyticsService) -> None:
        self._analytics = analytics

    async def cuisine_stats(self, max_cook_time_min: int | None) -> AggregationReportDTO:
        report = await self._analytics.cuisine_stats(max_cook_time_min)
        return AggregationReportDTO.model_validate(asdict(report))
