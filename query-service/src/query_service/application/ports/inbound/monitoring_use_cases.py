"""Вхідні порти панелі моніторингу."""

from abc import ABC, abstractmethod

from query_service.application.dto import IngestConfigDTO, StatsDTO


class StatsQueryUseCase(ABC):
    @abstractmethod
    async def get_stats(self) -> StatsDTO:
        """Поточна статистика системи (оновлюється на UI раз на секунду)."""


class GeneratorControlUseCase(ABC):
    @abstractmethod
    async def get_config(self) -> IngestConfigDTO: ...

    @abstractmethod
    async def update_config(self, config: IngestConfigDTO) -> IngestConfigDTO:
        """Зберегти нову швидкість / стан Старт-Стоп (значення слайдера з UI)."""
