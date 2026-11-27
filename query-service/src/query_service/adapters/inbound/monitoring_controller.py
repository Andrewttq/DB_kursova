"""Вхідний адаптер — панель моніторингу та керування швидкістю.

Статистика оновлюється на UI опитуванням раз на секунду: HTMX сам надсилає
GET /ui/stats (атрибут hx-trigger="every 1s") і підставляє отриманий HTML.
Для частоти 1 раз/с це простіше за WebSocket і не потребує JavaScript.

Слайдер швидкості: HTMX надсилає форму (POST /ui/generator) при кожній зміні
слайдера чи натисканні Старт/Стоп. JSON-варіант для скриптів — PUT /api/generator.
"""

from typing import Annotated

from fastapi import APIRouter, Form, Request
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
        self.router.add_api_route(
            "/ui/generator", self.generator_html, methods=["GET"], response_class=HTMLResponse
        )
        self.router.add_api_route(
            "/ui/generator",
            self.generator_update_html,
            methods=["POST"],
            response_class=HTMLResponse,
        )

    async def get_stats(self) -> StatsDTO:
        return await self._stats.get_stats()

    async def get_config(self) -> IngestConfigDTO:
        return await self._generator.get_config()

    async def update_config(self, config: IngestConfigDTO) -> IngestConfigDTO:
        """PUT /api/generator — JSON {"rate_per_sec": 500, "running": true}."""
        return await self._generator.update_config(config)

    async def stats_html(self, request: Request) -> HTMLResponse:
        """Рендер шаблону partials/stats.html."""
        stats = await self._stats.get_stats()
        return self._templates.TemplateResponse(request, "partials/stats.html", {"stats": stats})

    async def generator_html(self, request: Request) -> HTMLResponse:
        config = await self._generator.get_config()
        return self._templates.TemplateResponse(
            request, "partials/generator.html", {"config": config}
        )

    async def generator_update_html(
        self,
        request: Request,
        rate: Annotated[int, Form()],
        running: Annotated[str, Form()] = "1",
    ) -> HTMLResponse:
        """Форма слайдера: rate — значення слайдера, running — "1" (Старт) або "0" (Стоп)."""
        config = await self._generator.update_config(
            IngestConfigDTO(rate_per_sec=max(10, min(5000, rate)), running=running != "0")
        )
        return self._templates.TemplateResponse(
            request, "partials/generator.html", {"config": config}
        )
