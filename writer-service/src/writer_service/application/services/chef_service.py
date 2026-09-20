"""Прикладний сервіс для шефів."""

from writer_service.application.ports.outbound.chef_repositories import ChefRepository
from writer_service.domain.chef import Chef


class ChefService:
    def __init__(self, repository: ChefRepository) -> None:
        self._repository = repository

    async def save_many(self, chefs: list[Chef]) -> int:
        """Зберегти шефів пачки (без дублікатів у межах пачки)."""
        raise NotImplementedError
