"""Вхідний порт — запити щодо шефів."""

from abc import ABC, abstractmethod

from query_service.application.dto import ChefProfileDTO


class ChefQueryUseCase(ABC):
    @abstractmethod
    async def get_chef_profile(self, chef_id: str) -> ChefProfileDTO | None:
        """Профіль шефа разом із його рецептами."""
