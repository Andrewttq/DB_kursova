"""Прикладні сервіси для читання рецептів."""

import logging

from query_service.application.ports.outbound.recipe_repositories import (
    RecipeGraphReadRepository,
    RecipeReadRepository,
)
from query_service.domain.recipe import Recipe, Recommendation

logger = logging.getLogger(__name__)


class RecipeInformationService:
    """Картки рецептів із MongoDB."""

    def __init__(self, repository: RecipeReadRepository) -> None:
        self._repository = repository

    async def get(self, recipe_id: str) -> Recipe | None:
        return await self._repository.find_by_id(recipe_id)

    async def get_many(self, recipe_ids: list[str]) -> list[Recipe]:
        return await self._repository.find_by_ids(recipe_ids)

    async def by_chef(self, chef_id: str, limit: int) -> list[Recipe]:
        """Рецепти шефа напряму з MongoDB (запасний шлях, якщо граф ще порожній)."""
        return await self._repository.find_by_chef(chef_id, limit)

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
    """Рекомендації та зв'язки з Neo4j.

    Рекомендації — додаткова інформація, тому якщо Neo4j недоступний,
    сторінка рецепта все одно має відкритися: повертаємо порожній список
    і пишемо WARNING у лог, а не падаємо з помилкою 500.
    """

    def __init__(self, graph: RecipeGraphReadRepository) -> None:
        self._graph = graph

    async def similar(self, recipe_id: str, limit: int) -> list[Recommendation]:
        try:
            return await self._graph.find_similar_by_ingredients(recipe_id, limit)
        except Exception as exc:  # noqa: BLE001 — будь-яка помилка графа не повинна ламати сторінку
            logger.warning("Neo4j недоступний, рекомендацій не буде: %s", exc)
            return []

    async def recipe_ids_of_chef(self, chef_id: str, limit: int) -> list[str]:
        try:
            return await self._graph.find_recipe_ids_by_chef(chef_id, limit)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Neo4j недоступний, рецепти шефа візьмемо з MongoDB: %s", exc)
            return []
