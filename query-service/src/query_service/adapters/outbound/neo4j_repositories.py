"""Вихідний адаптер Neo4j для читання."""

from neo4j import AsyncDriver

from query_service.application.ports.outbound.recipe_repositories import (
    RecipeGraphReadRepository,
)
from query_service.domain.recipe import Recommendation


class Neo4jRecipeGraphReadRepository(RecipeGraphReadRepository):
    """Реалізує RecipeGraphReadRepository.

    Схожі рецепти — обхід графа на 2 кроки:
        MATCH (r:Recipe {id: $id})-[:CONTAINS]->(i:Ingredient)<-[:CONTAINS]-(o:Recipe)
        WHERE o <> r
        RETURN o.id AS id, o.title AS title, count(i) AS common
        ORDER BY common DESC LIMIT $limit
    У реляційній БД це був би self-join таблиці recipe_ingredients з групуванням.
    """

    def __init__(self, driver: AsyncDriver) -> None:
        self._driver = driver

    async def find_similar_by_ingredients(self, recipe_id: str, limit: int) -> list[Recommendation]:
        raise NotImplementedError

    async def find_recipe_ids_by_chef(self, chef_id: str, limit: int) -> list[str]:
        raise NotImplementedError
