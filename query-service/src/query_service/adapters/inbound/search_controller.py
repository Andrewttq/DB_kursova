"""Вхідний адаптер — пошук.

Два маршрути з однаковою логікою:
    GET /api/search      — JSON (для тестів і нагрузочного тестування Locust);
    GET /ui/search       — HTML-фрагмент для HTMX (результати підставляються на сторінку).
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from query_service.application.dto import SearchResponseDTO
from query_service.application.ports.inbound.search_use_case import SearchRecipesUseCase


class SearchController:
    def __init__(self, use_case: SearchRecipesUseCase, templates: Jinja2Templates) -> None:
        self._use_case = use_case
        self._templates = templates
        self.router = APIRouter(tags=["search"])
        self.router.add_api_route("/api/search", self.search_json, methods=["GET"])
        self.router.add_api_route(
            "/ui/search", self.search_html, methods=["GET"], response_class=HTMLResponse
        )

    async def search_json(
        self, q: str, cuisine: str | None = None, max_cook_time_min: int | None = None
    ) -> SearchResponseDTO:
        raise NotImplementedError

    async def search_html(self, request: Request, q: str) -> HTMLResponse:
        """Рендер шаблону partials/search_results.html."""
        raise NotImplementedError
