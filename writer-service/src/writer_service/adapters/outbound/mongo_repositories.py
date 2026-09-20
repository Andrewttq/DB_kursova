"""Вихідні адаптери MongoDB (асинхронний драйвер PyMongo: AsyncMongoClient).

Підключення йде до маршрутизатора mongos, а не до окремого шарда:
mongos сам визначає за ключем шардування, на який шард записати документ.
Колекція recipes шардована за ключем { _id: "hashed" }.
"""

from pymongo import AsyncMongoClient

from writer_service.application.ports.outbound.chef_repositories import ChefRepository
from writer_service.application.ports.outbound.recipe_repositories import (
    RecipeDocumentRepository,
)
from writer_service.domain.chef import Chef
from writer_service.domain.recipe import Recipe


class MongoRecipeRepository(RecipeDocumentRepository):
    """Реалізує RecipeDocumentRepository.

    upsert_many: bulk_write із ReplaceOne(upsert=True) і ordered=False —
    при ordered=False помилка одного документа не зупиняє запис решти,
    а mongos може паралельно відправляти частини пачки на різні шарди.
    """

    def __init__(self, client: AsyncMongoClient, db_name: str) -> None:
        self._collection = client[db_name]["recipes"]

    async def upsert_many(self, recipes: list[Recipe]) -> int:
        raise NotImplementedError

    async def delete(self, recipe_id: str) -> bool:
        raise NotImplementedError


class MongoChefRepository(ChefRepository):
    """Реалізує ChefRepository. Колекція chefs невелика і не шардується."""

    def __init__(self, client: AsyncMongoClient, db_name: str) -> None:
        self._collection = client[db_name]["chefs"]

    async def upsert_many(self, chefs: list[Chef]) -> int:
        raise NotImplementedError
