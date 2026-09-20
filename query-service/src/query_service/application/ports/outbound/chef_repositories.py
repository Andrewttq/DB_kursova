"""Вихідний порт для читання шефів."""

from abc import ABC, abstractmethod

from query_service.domain.chef import Chef


class ChefReadRepository(ABC):
    """Профілі шефів (реалізація: MongoChefReadRepository)."""

    @abstractmethod
    async def find_by_id(self, chef_id: str) -> Chef | None: ...
