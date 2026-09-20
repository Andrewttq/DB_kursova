"""Вихідний порт — конфігурація швидкості.

Швидкість задає користувач слайдером на UI. query-service записує її у сховище,
а ingest-service читає звідти. Так два сервіси обмінюються налаштуванням,
не викликаючи один одного напряму.
"""

from abc import ABC, abstractmethod


class IngestConfigPort(ABC):
    @abstractmethod
    async def get_rate(self) -> int:
        """Поточна швидкість у записах за секунду (10..5000)."""

    @abstractmethod
    async def is_running(self) -> bool:
        """Чи увімкнено завантаження (кнопка «Старт/Стоп» на UI)."""
