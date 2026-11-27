"""Вхідний порт — аналітичні запити по всіх шардах (завдання 14)."""

from abc import ABC, abstractmethod

from query_service.application.dto import AggregationReportDTO


class RecipeAnalyticsUseCase(ABC):
    @abstractmethod
    async def cuisine_stats(self, max_cook_time_min: int | None) -> AggregationReportDTO:
        """Кількість рецептів, середні калорії й час для кожної кухні."""
