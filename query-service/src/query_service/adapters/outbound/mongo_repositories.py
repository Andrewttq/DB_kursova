"""Вихідні адаптери MongoDB для читання (асинхронний PyMongo)."""

from dataclasses import fields

from pymongo import AsyncMongoClient

from query_service.application.ports.outbound.chef_repositories import ChefReadRepository
from query_service.application.ports.outbound.recipe_repositories import RecipeReadRepository
from query_service.domain.chef import Chef
from query_service.domain.recipe import Recipe

# Беремо з документа лише відомі поля: зайве поле в базі нічого не зламає.
_RECIPE_FIELDS = {f.name for f in fields(Recipe)}


def _to_recipe(doc: dict) -> Recipe:
    """Перетворити документ MongoDB на доменний Recipe (_id -> id)."""
    doc = dict(doc)
    doc["id"] = doc.pop("_id")
    return Recipe(**{k: v for k, v in doc.items() if k in _RECIPE_FIELDS})


def _to_chef(doc: dict) -> Chef:
    """Перетворити документ MongoDB на доменний Chef (_id -> id)."""
    return Chef(id=doc["_id"], full_name=doc.get("full_name", "невідомий автор"))


class MongoRecipeReadRepository(RecipeReadRepository):
    """Реалізує RecipeReadRepository.

    find_by_id — адресний (targeted) запит: mongos обчислює хеш _id
    і звертається лише до одного шарда.
    find_by_filter — запит до всіх шардів (scatter-gather), тому потрібен
    індекс { cuisine: 1, cook_time_min: 1, calories: 1 }. Перевірити план: .explain().
    find_by_chef — теж scatter-gather, використовує індекс { chef_id: 1 }.
    """

    def __init__(self, client: AsyncMongoClient, db_name: str) -> None:
        self._collection = client[db_name]["recipes"]

    async def find_by_id(self, recipe_id: str) -> Recipe | None:
        doc = await self._collection.find_one({"_id": recipe_id})
        return _to_recipe(doc) if doc is not None else None

    async def find_by_ids(self, recipe_ids: list[str]) -> list[Recipe]:
        if not recipe_ids:
            return []
        cursor = self._collection.find({"_id": {"$in": recipe_ids}})
        by_id = {r.id: r for r in (_to_recipe(doc) for doc in await cursor.to_list())}
        # $in не зберігає порядок, тому відновлюємо порядок вхідного списку.
        return [by_id[rid] for rid in recipe_ids if rid in by_id]

    async def find_by_chef(self, chef_id: str, limit: int) -> list[Recipe]:
        cursor = self._collection.find({"chef_id": chef_id}).limit(limit)
        return [_to_recipe(doc) for doc in await cursor.to_list()]

    async def find_by_filter(
        self,
        cuisine: str | None,
        max_cook_time_min: int | None,
        max_calories: float | None,
        skip: int,
        limit: int,
    ) -> list[Recipe]:
        query: dict = {}
        if cuisine:
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
        return [_to_recipe(doc) for doc in await cursor.to_list()]


class MongoChefReadRepository(ChefReadRepository):
    def __init__(self, client: AsyncMongoClient, db_name: str) -> None:
        self._collection = client[db_name]["chefs"]

    async def find_by_id(self, chef_id: str) -> Chef | None:
        doc = await self._collection.find_one({"_id": chef_id})
        return _to_chef(doc) if doc is not None else None
