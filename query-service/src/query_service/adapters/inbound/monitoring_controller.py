"""Вхідний адаптер — панель моніторингу та керування швидкістю.

Статистика оновлюється на UI опитуванням раз на секунду: HTMX сам надсилає
GET /ui/stats (атрибут hx-trigger="every 1s") і підставляє отриманий HTML.
Для частоти 1 раз/с це простіше за WebSocket і не потребує JavaScript.
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from query_service.application.dto import IngestConfigDTO, StatsDTO
from query_service.application.ports.inbound.monitoring_use_cases import (
    GeneratorControlUseCase,
    StatsQueryUseCase,
)


class MonitoringController:
    def __init__(
        self,
        stats: StatsQueryUseCase,
        generator: GeneratorControlUseCase,
        templates: Jinja2Templates,
    ) -> None:
        self._stats = stats
        self._generator = generator
        self._templates = templates
        self.router = APIRouter(tags=["monitoring"])
        self.router.add_api_route("/api/stats", self.get_stats, methods=["GET"])
        self.router.add_api_route("/api/generator", self.get_config, methods=["GET"])
        self.router.add_api_route("/api/generator", self.update_config, methods=["PUT"])
        self.router.add_api_route(
            "/ui/stats", self.stats_html, methods=["GET"], response_class=HTMLResponse
        )

    async def get_stats(self) -> StatsDTO:
        raise NotImplementedError

    async def get_config(self) -> IngestConfigDTO:
        raise NotImplementedError

    async def update_config(self, config: IngestConfigDTO) -> IngestConfigDTO:
        """PUT /api/generator — викликається при зміні слайдера."""
        raise NotImplementedError

    async def stats_html(self, request: Request) -> HTMLResponse:
        """Рендер шаблону partials/stats.html."""
        raise NotImplementedError
