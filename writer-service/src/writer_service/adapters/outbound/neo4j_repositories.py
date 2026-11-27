"""Вихідний адаптер Neo4j (асинхронний драйвер)."""

import logging

from neo4j import AsyncDriver

from writer_service.application.ports.outbound.recipe_repositories import RecipeGraphRepository
from writer_service.domain.recipe import Recipe

logger = logging.getLogger(__name__)

# Обмеження унікальності: MERGE шукає вузол за id/name через індекс, який створює constraint.
# Без них кожен MERGE перебирав би всі вузли мітки — запис сповільнився б у сотні разів.
CONSTRAINTS = [
    "CREATE CONSTRAINT recipe_id IF NOT EXISTS FOR (r:Recipe) REQUIRE r.id IS UNIQUE",
    "CREATE CONSTRAINT chef_id IF NOT EXISTS FOR (c:Chef) REQUIRE c.id IS UNIQUE",
    "CREATE CONSTRAINT ingredient_name IF NOT EXISTS FOR (i:Ingredient) REQUIRE i.name IS UNIQUE",
    "CREATE CONSTRAINT cuisine_name IF NOT EXISTS FOR (k:Cuisine) REQUIRE k.name IS UNIQUE",
]

MERGE_QUERY = """
UNWIND $rows AS row
MERGE (r:Recipe {id: row.id})
SET r.title = row.title
MERGE (c:Chef {id: row.chef_id})
MERGE (c)-[:CREATED]->(r)
FOREACH (cuisine IN CASE WHEN row.cuisine IS NULL THEN [] ELSE [row.cuisine] END |
    MERGE (k:Cuisine {name: cuisine})
    MERGE (r)-[:BELONGS_TO]->(k))
WITH r, row
UNWIND row.ingredients AS name
MERGE (i:Ingredient {name: name})
MERGE (r)-[:CONTAINS]->(i)
WITH DISTINCT i
SET i.recipe_count = COUNT { (i)<-[:CONTAINS]-(:Recipe) }
RETURN count(i) AS ingredients
"""

DELETE_QUERY = "MATCH (r:Recipe {id: $id}) DETACH DELETE r"


class Neo4jRecipeGraphRepository(RecipeGraphRepository):
    """Реалізує RecipeGraphRepository.

    merge_many — один Cypher-запит на всю пачку через UNWIND
    (замість сотень окремих запитів). MERGE, а не CREATE — щоб повторний запис
    не створював дублікатів (ідемпотентність).
    Після запису оновлюється recipe_count інгредієнтів пачки: query-service
    за ним відкидає надто часті інгредієнти (salt, sugar) у рекомендаціях.
    """

    def __init__(self, driver: AsyncDriver) -> None:
        self._driver = driver

    async def ensure_schema(self) -> None:
        """Створити constraints (викликається при старті екземпляра з роллю neo4j)."""
        for statement in CONSTRAINTS:
            await self._driver.execute_query(statement)
        logger.info("Constraints Neo4j створено або вже існують")

    async def merge_many(self, recipes: list[Recipe]) -> int:
        if not recipes:
            return 0
        rows = [
            {
                "id": r.id,
                "title": r.title,
                "chef_id": r.chef_id,
                "cuisine": r.cuisine,
                # унікальні непорожні інгредієнти, інакше MERGE (i {name: ""}) створить сміття
                "ingredients": sorted({i.strip().lower() for i in r.ingredients if i.strip()}),
            }
            for r in recipes
        ]
        await self._driver.execute_query(MERGE_QUERY, rows=rows)
        return len(recipes)

    async def delete(self, recipe_id: str) -> None:
        await self._driver.execute_query(DELETE_QUERY, id=recipe_id)
