"""Фасад — реалізація ChefQueryUseCase.

Профіль шефа збирається з двох БД:
    ChefController -> ChefQueryFacade -> ChefService (MongoDB, профіль)
                                      -> RecipeRelationService (Neo4j, id рецептів шефа)
                                      -> RecipeInformationService (MongoDB, картки за id)
Якщо граф ще не наповнений (немає зв'язків CREATED), рецепти беруться напряму з MongoDB.
"""

from query_service.application import mappers
from query_service.application.dto import ChefProfileDTO
from query_service.application.ports.inbound.chef_use_cases import ChefQueryUseCase
from query_service.application.services.chef_service import ChefService
from query_service.application.services.recipe_services import (
    RecipeInformationService,
    RecipeRelationService,
)

MAX_RECIPES_ON_PROFILE = 50


class ChefQueryFacade(ChefQueryUseCase):
    def __init__(
        self,
        chefs: ChefService,
        relations: RecipeRelationService,
        recipes: RecipeInformationService,
    ) -> None:
        self._chefs = chefs
        self._relations = relations
        self._recipes = recipes

    async def get_chef_profile(self, chef_id: str) -> ChefProfileDTO | None:
        chef = await self._chefs.get(chef_id)
        if chef is None:
            return None
        ids = await self._relations.recipe_ids_of_chef(chef_id, MAX_RECIPES_ON_PROFILE)
        if ids:
            recipes = await self._recipes.get_many(ids)
        else:
            recipes = await self._recipes.by_chef(chef_id, MAX_RECIPES_ON_PROFILE)
        return ChefProfileDTO(
            id=chef.id,
            full_name=chef.full_name,
            recipes=[mappers.recipe_to_short_dto(r) for r in mappers.unique_by_title(recipes)],
        )
