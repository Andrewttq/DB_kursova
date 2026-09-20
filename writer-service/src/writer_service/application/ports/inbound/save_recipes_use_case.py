"""Вхідний порт — команда «зберегти пачку рецептів» (Command у термінах CQRS).

CQRS ділить операції на команди (змінюють дані) і запити (лише читають).
Цей сервіс містить тільки команди, усі запити — у query-service.
"""

from abc import ABC, abstractmethod

from contracts import RecipeIngestedEvent


class SaveRecipesUseCase(ABC):
    @abstractmethod
    async def save_batch(self, events: list[RecipeIngestedEvent]) -> int:
        """Зберегти пачку рецептів у всі сховища. Повертає кількість збережених."""
