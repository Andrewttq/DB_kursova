"""Вхідний порт — повнотекстовий пошук рецептів."""

from abc import ABC, abstractmethod

from query_service.application.dto import SearchRequestDTO, SearchResponseDTO


class SearchRecipesUseCase(ABC):
    @abstractmethod
    async def search(self, request: SearchRequestDTO) -> SearchResponseDTO:
        """Пошук із кешуванням. Порожній результат — це нормальна відповідь, а не помилка."""
