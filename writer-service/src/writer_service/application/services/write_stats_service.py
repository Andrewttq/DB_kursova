"""Прикладний сервіс статистики запису."""

import logging

from writer_service.application.ports.outbound.stats_repositories import WriteStatsRepository

logger = logging.getLogger(__name__)


class WriteStatsService:
    def __init__(self, repository: WriteStatsRepository) -> None:
        self._repository = repository

    async def on_saved(self, count: int) -> None:
        await self._repository.incr_saved(count)

    async def on_failed(self, count: int) -> None:
        # Статистика не повинна заважати основній роботі: якщо Redis впав,
        # просто пишемо в лог (сама помилка запису вже буде оброблена фасадом).
        try:
            await self._repository.incr_failed(count)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Не вдалося оновити лічильник помилок: %s", exc)
