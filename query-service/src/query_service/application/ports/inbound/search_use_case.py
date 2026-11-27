"""Вхідний порт — повнотекстовий пошук рецептів."""

from abc import ABC, abstractmethod

from query_service.application.dto import SearchLogDTO, SearchRequestDTO, SearchResponseDTO


class SearchRecipesUseCase(ABC):
    @abstractmethod
    async def search(self, request: SearchRequestDTO) -> SearchResponseDTO:
        """Пошук із кешуванням. Порожній результат — це нормальна відповідь, а не помилка."""

    @abstractmethod
    async def recent_searches(self, limit: int) -> list[SearchLogDTO]:
        """Останні пошукові запити (блок «Останні запити» на UI)."""
