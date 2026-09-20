"""Фасад — реалізація RecipeQueryUseCase.

Ланцюжок виклику картки рецепта:
    RecipeController -> RecipeQueryFacade -> RecipeInformationService (MongoDB)
                                          + ChefService (MongoDB, ім'я автора)
                                          + RecipeRelationService (Neo4j, рекомендації)
Фасад поєднує дані з кількох сховищ в одну відповідь для UI.
"""

from query_service.application.dto import (
    RecipeCardDTO,
    RecipeFilterDTO,
    RecipeShortDTO,
    RecommendationDTO,
)
from query_service.application.ports.inbound.recipe_use_cases import RecipeQueryUseCase
from query_service.application.services.chef_service import ChefService
from query_service.application.services.recipe_services import (
    RecipeInformationService,
    RecipeRelationService,
)


class RecipeQueryFacade(RecipeQueryUseCase):
    def __init__(
        self,
        recipes: RecipeInformationService,
        chefs: ChefService,
        relations: RecipeRelationService,
    ) -> None:
        self._recipes = recipes
        self._chefs = chefs
        self._relations = relations

    async def get_recipe_card(self, recipe_id: str) -> RecipeCardDTO | None:
        """recipes.get -> chefs.get(recipe.chef_id) -> mappers.recipe_to_card_dto."""
        raise NotImplementedError

    async def list_recipes(self, flt: RecipeFilterDTO) -> list[RecipeShortDTO]:
        raise NotImplementedError

    async def get_recommendations(self, recipe_id: str, limit: int) -> list[RecommendationDTO]:
        raise NotImplementedError
