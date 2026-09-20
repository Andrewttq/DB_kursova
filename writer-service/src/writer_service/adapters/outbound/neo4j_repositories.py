"""Вихідний адаптер Neo4j (асинхронний драйвер)."""

from neo4j import AsyncDriver

from writer_service.application.ports.outbound.recipe_repositories import RecipeGraphRepository
from writer_service.domain.recipe import Recipe


class Neo4jRecipeGraphRepository(RecipeGraphRepository):
    """Реалізує RecipeGraphRepository.

    merge_many — один Cypher-запит на всю пачку через UNWIND
    (замість сотень окремих запитів):
        UNWIND $rows AS row
        MERGE (r:Recipe {id: row.id}) SET r.title = row.title
        MERGE (c:Chef {id: row.chef_id})
        MERGE (c)-[:CREATED]->(r)
        WITH r, row UNWIND row.ingredients AS name
        MERGE (i:Ingredient {name: name})
        MERGE (r)-[:CONTAINS]->(i)
    MERGE, а не CREATE — щоб повторний запис не створював дублікатів.
    Для швидкості потрібні constraints на Recipe.id, Chef.id, Ingredient.name.
    """

    def __init__(self, driver: AsyncDriver) -> None:
        self._driver = driver

    async def merge_many(self, recipes: list[Recipe]) -> int:
        raise NotImplementedError

    async def delete(self, recipe_id: str) -> None:
        raise NotImplementedError
