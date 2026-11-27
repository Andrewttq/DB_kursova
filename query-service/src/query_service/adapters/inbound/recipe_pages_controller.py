"""Вхідний адаптер — HTML-сторінки рецептів і шефів (завдання 12).

Повний шлях запиту, наприклад для сторінки рецепта:
    браузер -> GET /recipes/{id} -> RecipePagesController (цей файл)
            -> RecipeQueryUseCase (інтерфейс) -> RecipeQueryFacade
            -> RecipeInformationService / ChefService -> порти
            -> MongoRecipeReadRepository / MongoChefReadRepository -> MongoDB
    і назад: Recipe -> RecipeCardDTO -> шаблон recipe.html -> HTML у браузер.

Контролер працює з тими самими вхідними портами, що й REST-контролери,
тобто JSON API і HTML-сторінки використовують одну бізнес-логіку.
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from query_service.application.dto import RecipeFilterDTO
from query_service.application.ports.inbound.chef_use_cases import ChefQueryUseCase
from query_service.application.ports.inbound.recipe_use_cases import RecipeQueryUseCase

# Кухні, які вміє визначати ingest-service (для підказки у фільтрі).
CUISINES = [
    "american", "italian", "mexican", "asian", "european", "french", "greek", "indian",
    "chinese", "thai", "japanese", "spanish", "german", "middle-eastern", "african",
    "caribbean", "korean", "vietnamese", "british", "irish", "canadian", "australian",
    "russian", "polish", "scandinavian", "turkish", "moroccan", "brazilian", "cajun",
    "southwestern-united-states",
]  # fmt: skip

PAGE_SIZE = 20


def _int_or_none(value: str | None) -> int | None:
    """Порожнє поле форми приходить як "", а не None — перетворюємо самі."""
    return int(value) if value and value.strip().isdigit() else None


class RecipePagesController:
    def __init__(
        self,
        recipes: RecipeQueryUseCase,
        chefs: ChefQueryUseCase,
        templates: Jinja2Templates,
    ) -> None:
        self._recipes = recipes
        self._chefs = chefs
        self._templates = templates
        self.router = APIRouter(include_in_schema=False)
        html = {"methods": ["GET"], "response_class": HTMLResponse}
        self.router.add_api_route("/recipes", self.recipes_page, **html)
        self.router.add_api_route("/ui/recipes", self.recipes_fragment, **html)
        self.router.add_api_route("/recipes/{recipe_id}", self.recipe_page, **html)
        self.router.add_api_route("/ui/recipes/{recipe_id}/similar", self.similar_fragment, **html)
        self.router.add_api_route("/chefs/{chef_id}", self.chef_page, **html)

    async def recipes_page(self, request: Request) -> HTMLResponse:
        """Сторінка зі списком і формою фільтрів; сам список підвантажує HTMX."""
        return self._templates.TemplateResponse(request, "recipes.html", {"cuisines": CUISINES})

    async def recipes_fragment(
        self,
        request: Request,
        cuisine: str | None = None,
        max_cook_time_min: str | None = None,
        max_calories: str | None = None,
        page: int = 1,
    ) -> HTMLResponse:
        """Фрагмент списку рецептів (partials/recipe_list.html) з пагінацією."""
        flt = RecipeFilterDTO(
            cuisine=cuisine or None,
            max_cook_time_min=_int_or_none(max_cook_time_min),
            max_calories=_int_or_none(max_calories),
            page=max(page, 1),
            size=PAGE_SIZE,
        )
        recipes = await self._recipes.list_recipes(flt)
        return self._templates.TemplateResponse(
            request,
            "partials/recipe_list.html",
            {"recipes": recipes, "flt": flt, "has_next": len(recipes) == PAGE_SIZE},
        )

    async def recipe_page(self, request: Request, recipe_id: str) -> HTMLResponse:
        card = await self._recipes.get_recipe_card(recipe_id)
        if card is None:
            return self._templates.TemplateResponse(
                request,
                "not_found.html",
                {"what": "Рецепт", "item_id": recipe_id},
                status_code=404,
            )
        return self._templates.TemplateResponse(request, "recipe.html", {"card": card})

    async def similar_fragment(self, request: Request, recipe_id: str) -> HTMLResponse:
        """Блок «Схожі рецепти» підвантажується окремим запитом після відкриття сторінки,
        тому повільний граф не затримує показ самої картки."""
        recs = await self._recipes.get_recommendations(recipe_id, 5)
        return self._templates.TemplateResponse(request, "partials/similar.html", {"recs": recs})

    async def chef_page(self, request: Request, chef_id: str) -> HTMLResponse:
        profile = await self._chefs.get_chef_profile(chef_id)
        if profile is None:
            return self._templates.TemplateResponse(
                request,
                "not_found.html",
                {"what": "Шеф", "item_id": chef_id},
                status_code=404,
            )
        return self._templates.TemplateResponse(request, "chef.html", {"profile": profile})
