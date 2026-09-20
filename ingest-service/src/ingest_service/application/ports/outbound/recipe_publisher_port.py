"""Вихідний порт — публікація рецептів для інших сервісів."""

from abc import ABC, abstractmethod

from ingest_service.domain.raw_recipe import RawRecipe


class RecipePublisherPort(ABC):
    @abstractmethod
    async def publish_batch(self, recipes: list[RawRecipe]) -> int:
        """Опублікувати пачку рецептів. Повертає кількість успішно опублікованих."""
