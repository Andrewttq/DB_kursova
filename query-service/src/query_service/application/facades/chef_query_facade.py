"""Фасад — реалізація ChefQueryUseCase.

Профіль шефа збирається з двох БД:
    ChefController -> ChefQueryFacade -> ChefService (MongoDB, профіль)
                                      -> RecipeRelationService (Neo4j, id рецептів шефа)
                                      -> RecipeInformationService (MongoDB, картки за id)
"""

from query_service.application.dto import ChefProfileDTO
from query_service.application.ports.inbound.chef_use_cases import ChefQueryUseCase
from query_service.application.services.chef_service import ChefService
from query_service.application.services.recipe_services import (
    RecipeInformationService,
    RecipeRelationService,
)


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
        raise NotImplementedError
