"""Прикладний сервіс для шефів."""

from query_service.application.ports.outbound.chef_repositories import ChefReadRepository
from query_service.domain.chef import Chef


class ChefService:
    def __init__(self, repository: ChefReadRepository) -> None:
        self._repository = repository

    async def get(self, chef_id: str) -> Chef | None:
        raise NotImplementedError
