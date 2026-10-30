"""Вихідні адаптери MongoDB для читання (асинхронний PyMongo)."""

from pymongo import AsyncMongoClient


from query_service.application.ports.outbound.chef_repositories import ChefReadRepository
from query_service.application.ports.outbound.recipe_repositories import RecipeReadRepository
from query_service.domain.chef import Chef
from query_service.domain.recipe import Recipe


def _to_recipe(doc: dict) -> Recipe:
    """Перетворити документ MongoDB на доменний Recipe (_id -> id)."""
    recipe_id = doc.pop("_id")
    return Recipe(id=recipe_id, **doc)


def _to_chef(doc: dict) -> Chef:
    """Перетворити документ MongoDB на доменний Chef (_id -> id)."""
    chef_id = doc.pop("_id")
    return Chef(id=chef_id, **doc)


class MongoRecipeReadRepository(RecipeReadRepository):
    """Реалізує RecipeReadRepository.

    find_by_id — адресний (targeted) запит: mongos обчислює хеш _id
    і звертається лише до одного шарда.
    find_by_filter — запит до всіх шардів (scatter-gather), тому потрібен
    індекс { cuisine: 1, cook_time_min: 1, calories: 1 }. Перевірити план: .explain().
    """

    def __init__(self, client: AsyncMongoClient, db_name: str) -> None:
        self._collection = client[db_name]["recipes"]

    async def find_by_id(self, recipe_id: str) -> Recipe | None:
        doc = await self._collection.find_one({"_id": recipe_id})
        if doc is not None:
            return _to_recipe(doc)
        return None

    async def find_by_ids(self, recipe_ids: list[str]) -> list[Recipe]:
        if not recipe_ids:
            return []
        cursor = self._collection.find({"_id": {"$in": recipe_ids}})
        docs = await cursor.to_list()

        recipes = [_to_recipe(doc) for doc in docs]
        by_id = {recipe.id: recipe for recipe in recipes}
        return [by_id[rid] for rid in recipe_ids if rid in by_id]

    async def find_by_filter(
        self,
        cuisine: str | None,
        max_cook_time_min: int | None,
        max_calories: float | None,
        skip: int,
        limit: int,
    ) -> list[Recipe]:
        query = {}
        if cuisine is not None:
            query["cuisine"] = cuisine
        if max_cook_time_min is not None:
            query["cook_time_min"] = {"$lte": max_cook_time_min}
        if max_calories is not None:
            query["calories"] = {"$lte": max_calories}

        cursor = (
            self._collection.find(query)
            .sort([("cook_time_min", 1), ("_id", 1)])
            .skip(skip)
            .limit(limit)
        )
        docs = await cursor.to_list()
        return [_to_recipe(doc) for doc in docs]


class MongoChefReadRepository(ChefReadRepository):
    def __init__(self, client: AsyncMongoClient, db_name: str) -> None:
        self._collection = client[db_name]["chefs"]

    async def find_by_id(self, chef_id: str) -> Chef | None:
        doc = await self._collection.find_one({"_id": chef_id})
        if doc is not None:
            return _to_chef(doc)
        return None
