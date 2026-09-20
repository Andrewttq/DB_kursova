"""Вихідний порт для шефів."""

from abc import ABC, abstractmethod

from writer_service.domain.chef import Chef


class ChefRepository(ABC):
    """Профілі шефів у документній БД (реалізація: MongoChefRepository)."""

    @abstractmethod
    async def upsert_many(self, chefs: list[Chef]) -> int: ...
