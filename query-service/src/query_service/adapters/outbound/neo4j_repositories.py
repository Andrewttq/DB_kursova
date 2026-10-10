"""Вихідний адаптер Neo4j для читання."""

from neo4j import AsyncDriver

from query_service.application.ports.outbound.recipe_repositories import (
    RecipeGraphReadRepository,
)
from query_service.domain.recipe import Recommendation


class Neo4jRecipeGraphReadRepository(RecipeGraphReadRepository):
    """Реалізує RecipeGraphReadRepository.

    Схожі рецепти — обхід графа на 2 кроки:
        MATCH (r:Recipe {id: $id})-[:CONTAINS]->(i:Ingredient)
        WHERE i.recipe_count < 5000
        MATCH (i)<-[:CONTAINS]-(o:Recipe)
        WHERE o <> r
        RETURN o.id AS id, o.title AS title, count(i) AS common_ingredients,
               sum(1.0 / i.recipe_count) AS score
        ORDER BY score DESC LIMIT $limit
    Інгредієнти, що входять більш ніж у 5000 рецептів (salt, butter, sugar), не враховуються:
    обхід через них проходить сотні тисяч шляхів і нічого не каже про схожість.
    Решта зважується за рідкісністю: внесок інгредієнта дорівнює 1 / recipe_count.
    У реляційній БД це був би self-join таблиці recipe_ingredients з групуванням.
    """

    def __init__(self, driver: AsyncDriver) -> None:
        self._driver = driver

    async def find_similar_by_ingredients(self, recipe_id: str, limit: int) -> list[Recommendation]:
        raise NotImplementedError

    async def find_recipe_ids_by_chef(self, chef_id: str, limit: int) -> list[str]:
        raise NotImplementedError
