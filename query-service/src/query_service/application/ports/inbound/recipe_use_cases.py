"""Вхідний порт — запити щодо рецептів (Query у термінах CQRS).

Тут лише операції читання. Команд (створити/змінити рецепт) у query-service немає:
дані в систему потрапляють тільки через ingest-service -> RabbitMQ -> writer-service.
"""

from abc import ABC, abstractmethod

from query_service.application.dto import (
    RecipeCardDTO,
    RecipeFilterDTO,
    RecipeShortDTO,
    RecommendationDTO,
)


class RecipeQueryUseCase(ABC):
    @abstractmethod
    async def get_recipe_card(self, recipe_id: str) -> RecipeCardDTO | None:
        """Повна картка рецепта або None, якщо не знайдено."""

    @abstractmethod
    async def list_recipes(self, flt: RecipeFilterDTO) -> list[RecipeShortDTO]:
        """Список рецептів за фільтрами (кухня, час, калорійність)."""

    @abstractmethod
    async def get_recommendations(self, recipe_id: str, limit: int) -> list[RecommendationDTO]:
        """Рецепти зі схожим набором інгредієнтів."""
