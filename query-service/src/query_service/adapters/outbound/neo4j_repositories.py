"""Вихідний адаптер Neo4j для читання."""

from neo4j import AsyncDriver

from query_service.application.ports.outbound.recipe_repositories import (
    RecipeGraphReadRepository,
)
from query_service.domain.recipe import Recommendation

# Інгредієнти, що входять у понад 5000 рецептів (salt, butter, sugar), не враховуються:
# обхід через них проходить сотні тисяч шляхів і нічого не каже про схожість.
# Решта зважується за рідкісністю: внесок інгредієнта дорівнює 1 / recipe_count.
SIMILAR_QUERY = """
MATCH (r:Recipe {id: $id})-[:CONTAINS]->(i:Ingredient)
WHERE coalesce(i.recipe_count, 1) < $max_ingredient_freq
MATCH (i)<-[:CONTAINS]-(o:Recipe)
WHERE o <> r
RETURN o.id AS id, o.title AS title,
       count(i) AS common_ingredients,
       sum(1.0 / coalesce(i.recipe_count, 1)) AS score
ORDER BY score DESC
LIMIT $limit
"""

CHEF_RECIPES_QUERY = """
MATCH (:Chef {id: $id})-[:CREATED]->(r:Recipe)
RETURN r.id AS id
ORDER BY r.title
LIMIT $limit
"""


class Neo4jRecipeGraphReadRepository(RecipeGraphReadRepository):
    """Реалізує RecipeGraphReadRepository.

    Схожі рецепти — обхід графа на 2 кроки (рецепт -> інгредієнт -> інший рецепт).
    У реляційній БД це був би self-join таблиці recipe_ingredients з групуванням.
    """

    def __init__(self, driver: AsyncDriver, max_ingredient_freq: int = 5000) -> None:
        self._driver = driver
        self._max_ingredient_freq = max_ingredient_freq

    async def find_similar_by_ingredients(self, recipe_id: str, limit: int) -> list[Recommendation]:
        records, _, _ = await self._driver.execute_query(
            SIMILAR_QUERY,
            id=recipe_id,
            limit=limit,
            max_ingredient_freq=self._max_ingredient_freq,
        )
        return [
            Recommendation(
                recipe_id=r["id"],
                title=r["title"] or r["id"],
                common_ingredients=r["common_ingredients"],
                score=r["score"],
            )
            for r in records
        ]

    async def find_recipe_ids_by_chef(self, chef_id: str, limit: int) -> list[str]:
        records, _, _ = await self._driver.execute_query(
            CHEF_RECIPES_QUERY, id=chef_id, limit=limit
        )
        return [r["id"] for r in records]
