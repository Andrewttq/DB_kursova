"""Прикладні сервіси для читання рецептів."""

from query_service.application.ports.outbound.recipe_repositories import (
    RecipeGraphReadRepository,
    RecipeReadRepository,
)
from query_service.domain.recipe import Recipe, Recommendation


class RecipeInformationService:
    """Картки рецептів із MongoDB."""

    def __init__(self, repository: RecipeReadRepository) -> None:
        self._repository = repository

    async def get(self, recipe_id: str) -> Recipe | None:
        return await self._repository.find_by_id(recipe_id)

    async def get_many(self, recipe_ids: list[str]) -> list[Recipe]:
        return await self._repository.find_by_ids(recipe_ids)

    async def filter(
        self,
        cuisine: str | None,
        max_cook_time_min: int | None,
        max_calories: float | None,
        page: int,
        size: int,
    ) -> list[Recipe]:
        """Перетворити page/size на skip/limit і звернутися до репозиторію."""

        skip = (page - 1) * size
        return await self._repository.find_by_filter(
            cuisine=cuisine,
            max_cook_time_min=max_cook_time_min,
            max_calories=max_calories,
            skip=skip,
            limit=size,
        )


class RecipeRelationService:
    """Рекомендації та зв'язки з Neo4j."""

    def __init__(self, graph: RecipeGraphReadRepository) -> None:
        self._graph = graph

    async def similar(self, recipe_id: str, limit: int) -> list[Recommendation]:
        raise NotImplementedError

    async def recipe_ids_of_chef(self, chef_id: str, limit: int) -> list[str]:
        raise NotImplementedError
