"""Вихідний порт аналітики (реалізація: MongoRecipeAnalyticsRepository)."""

from abc import ABC, abstractmethod

from query_service.domain.analytics import AggregationReport


class RecipeAnalyticsRepository(ABC):
    @abstractmethod
    async def cuisine_stats(self, max_cook_time_min: int | None) -> AggregationReport:
        """Статистика за кухнями по всій колекції (з усіх шардів) + план виконання."""
