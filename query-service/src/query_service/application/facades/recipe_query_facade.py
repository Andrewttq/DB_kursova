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
from query_service.application.mappers import recipe_to_card_dto, recipe_to_short_dto
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
        recipe = await self._recipes.get(recipe_id)
        if recipe is None:
            return None
        chef = await self._chefs.get(recipe.chef_id)
        chef_name = chef.full_name if chef is not None else "невідомий автор"
        return recipe_to_card_dto(recipe, chef_name)

    async def list_recipes(self, flt: RecipeFilterDTO) -> list[RecipeShortDTO]:
        recipes = await self._recipes.filter(
            flt.cuisine, flt.max_cook_time_min, flt.max_calories, flt.page, flt.size
        )
        return [recipe_to_short_dto(recipe) for recipe in recipes]

    async def get_recommendations(self, recipe_id: str, limit: int) -> list[RecommendationDTO]:
        raise NotImplementedError
