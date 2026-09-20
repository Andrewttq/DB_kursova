"""Вихідний порт — джерело рецептів.

Вихідний порт описує, що потрібно ядру від зовнішнього світу, не кажучи, як саме
це зроблено. Зараз його реалізує CsvRecipeSource. Якщо колись замінимо CSV
на генератор текстів або краулер, достатньо написати ще один адаптер —
IngestService при цьому не зміниться жодним рядком.
"""

from abc import ABC, abstractmethod

from ingest_service.domain.raw_recipe import RawRecipe


class RecipeSourcePort(ABC):
    @abstractmethod
    async def next_batch(self, size: int) -> list[RawRecipe]:
        """Повернути наступні `size` рецептів.

        Коли джерело закінчилося, має почати спочатку (з новими id),
        щоб потік даних не зупинявся під час демонстрації.
        """
