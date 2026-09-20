"""Вихідний порт — лічильники роботи сервісу для статистики на UI."""

from abc import ABC, abstractmethod


class IngestStatsPort(ABC):
    @abstractmethod
    async def incr_read(self, count: int) -> None:
        """Збільшити лічильник прочитаних із джерела записів."""

    @abstractmethod
    async def incr_published(self, count: int) -> None:
        """Збільшити лічильник опублікованих у брокер записів."""
