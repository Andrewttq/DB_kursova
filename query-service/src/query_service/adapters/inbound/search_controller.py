"""Вхідний адаптер — пошук.

Маршрути з однаковою логікою:
    GET /api/search          — JSON (для тестів і нагрузочного тестування Locust);
    GET /ui/search           — HTML-фрагмент для HTMX (результати підставляються на сторінку);
    GET /ui/search/recent    — HTML-фрагмент «Останні запити».
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from query_service.application.dto import SearchRequestDTO, SearchResponseDTO
from query_service.application.ports.inbound.search_use_case import SearchRecipesUseCase


def _num_or_none(value: str | None) -> int | None:
    return int(value) if value and value.strip().isdigit() else None


class SearchController:
    def __init__(self, use_case: SearchRecipesUseCase, templates: Jinja2Templates) -> None:
        self._use_case = use_case
        self._templates = templates
        self.router = APIRouter(tags=["search"])
        self.router.add_api_route("/api/search", self.search_json, methods=["GET"])
        self.router.add_api_route(
            "/ui/search", self.search_html, methods=["GET"], response_class=HTMLResponse
        )
        self.router.add_api_route(
            "/ui/search/recent", self.recent_html, methods=["GET"], response_class=HTMLResponse
        )

    async def search_json(
        self,
        q: str,
        cuisine: str | None = None,
        max_cook_time_min: int | None = None,
        max_calories: float | None = None,
        page: int = 1,
        size: int = 10,
    ) -> SearchResponseDTO:
        request = SearchRequestDTO(
            query=q,
            cuisine=cuisine,
            max_cook_time_min=max_cook_time_min,
            max_calories=max_calories,
            page=page,
            size=size,
        )
        return await self._use_case.search(request)

    async def search_html(
        self,
        request: Request,
        q: str = "",
        cuisine: str | None = None,
        max_cook_time_min: str | None = None,
        max_calories: str | None = None,
        page: int = 1,
    ) -> HTMLResponse:
        """Рендер шаблону partials/search_results.html."""
        if not q.strip():
            return HTMLResponse("")  # порожнє поле — нічого не показуємо
        try:
            dto = SearchRequestDTO(
                query=q,
                cuisine=cuisine or None,
                max_cook_time_min=_num_or_none(max_cook_time_min),
                max_calories=_num_or_none(max_calories),
                page=max(page, 1),
            )
        except ValidationError:
            return HTMLResponse("<p>Запит задовгий (максимум 200 символів).</p>")
        result = await self._use_case.search(dto)
        return self._templates.TemplateResponse(
            request, "partials/search_results.html", {"result": result, "req": dto}
        )

    async def recent_html(self, request: Request) -> HTMLResponse:
        entries = await self._use_case.recent_searches(10)
        return self._templates.TemplateResponse(
            request, "partials/recent_searches.html", {"entries": entries}
        )
