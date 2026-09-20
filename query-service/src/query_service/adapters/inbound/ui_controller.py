"""Вхідний адаптер — головна сторінка веб-інтерфейсу."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates


class UiController:
    def __init__(self, templates: Jinja2Templates) -> None:
        self._templates = templates
        self.router = APIRouter(include_in_schema=False)
        self.router.add_api_route("/", self.index, methods=["GET"], response_class=HTMLResponse)

    async def index(self, request: Request) -> HTMLResponse:
        return self._templates.TemplateResponse(request, "index.html")
