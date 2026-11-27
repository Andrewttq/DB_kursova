"""Вхідний адаптер — аналітика по всіх шардах (завдання 14).

GET /api/analytics/cuisines   — JSON: статистика за кухнями + як виконано запит;
GET /analytics                — сторінка з формою фільтра;
GET /ui/analytics             — HTML-фрагмент з таблицею (HTMX).
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from query_service.application.dto import AggregationReportDTO
from query_service.application.ports.inbound.analytics_use_case import RecipeAnalyticsUseCase


class AnalyticsController:
    def __init__(self, use_case: RecipeAnalyticsUseCase, templates: Jinja2Templates) -> None:
        self._use_case = use_case
        self._templates = templates
        self.router = APIRouter(tags=["analytics"])
        self.router.add_api_route("/api/analytics/cuisines", self.cuisines_json, methods=["GET"])
        self.router.add_api_route(
            "/analytics",
            self.page,
            methods=["GET"],
            response_class=HTMLResponse,
            include_in_schema=False,
        )
        self.router.add_api_route(
            "/ui/analytics",
            self.fragment,
            methods=["GET"],
            response_class=HTMLResponse,
            include_in_schema=False,
        )

    async def cuisines_json(self, max_cook_time_min: int | None = None) -> AggregationReportDTO:
        return await self._use_case.cuisine_stats(max_cook_time_min)

    async def page(self, request: Request) -> HTMLResponse:
        return self._templates.TemplateResponse(request, "analytics.html")

    async def fragment(
        self, request: Request, max_cook_time_min: str | None = None
    ) -> HTMLResponse:
        value = (max_cook_time_min or "").strip()
        limit = int(value) if value.isdigit() else None
        report = await self._use_case.cuisine_stats(limit)
        return self._templates.TemplateResponse(
            request, "partials/analytics_result.html", {"report": report}
        )
