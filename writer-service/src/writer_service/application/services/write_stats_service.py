"""Прикладний сервіс статистики запису."""

from writer_service.application.ports.outbound.stats_repositories import WriteStatsRepository


class WriteStatsService:
    def __init__(self, repository: WriteStatsRepository) -> None:
        self._repository = repository

    async def on_saved(self, count: int) -> None:
        raise NotImplementedError

    async def on_failed(self, count: int) -> None:
        raise NotImplementedError
