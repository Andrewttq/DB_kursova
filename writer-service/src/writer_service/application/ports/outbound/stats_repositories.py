"""Вихідний порт для статистики запису."""

from abc import ABC, abstractmethod


class WriteStatsRepository(ABC):
    """Лічильники запису (реалізація: RedisWriteStatsRepository)."""

    @abstractmethod
    async def incr_saved(self, count: int) -> None:
        """Збільшити загальний лічильник і лічильник поточної секунди (для write RPS)."""

    @abstractmethod
    async def incr_failed(self, count: int) -> None: ...
