"""Вхідний адаптер — REST-контролер рецептів.

Контролер лише перекладає HTTP на виклик вхідного порту і назад:
параметри запиту -> DTO -> use case -> DTO -> JSON. Жодної бізнес-логіки.
Контролер залежить від ІНТЕРФЕЙСУ RecipeQueryUseCase, а не від фасаду.
"""

from fastapi import APIRouter

from query_service.application.dto import (
    RecipeCardDTO,
    RecipeShortDTO,
    RecommendationDTO,
)
from query_service.application.ports.inbound.recipe_use_cases import RecipeQueryUseCase


class RecipeController:
    def __init__(self, use_case: RecipeQueryUseCase) -> None:
        self._use_case = use_case
        self.router = APIRouter(prefix="/api/recipes", tags=["recipes"])
        self.router.add_api_route("", self.list_recipes, methods=["GET"])
        self.router.add_api_route("/{recipe_id}", self.get_recipe, methods=["GET"])
        self.router.add_api_route(
            "/{recipe_id}/recommendations", self.get_recommendations, methods=["GET"]
        )

    async def list_recipes(
        self,
        cuisine: str | None = None,
        max_cook_time_min: int | None = None,
        max_calories: float | None = None,
        page: int = 1,
        size: int = 20,
    ) -> list[RecipeShortDTO]:
        """GET /api/recipes?cuisine=italian&max_cook_time_min=30

        Параметри зібрати в RecipeFilterDTO (він перевірить межі значень).
        """
        raise NotImplementedError

    async def get_recipe(self, recipe_id: str) -> RecipeCardDTO:
        """GET /api/recipes/{id}. Якщо use case повернув None — HTTP 404."""
        raise NotImplementedError

    async def get_recommendations(self, recipe_id: str, limit: int = 5) -> list[RecommendationDTO]:
        """GET /api/recipes/{id}/recommendations"""
        raise NotImplementedError
