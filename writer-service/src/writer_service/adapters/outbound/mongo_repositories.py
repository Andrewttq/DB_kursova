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
from pymongo import ReplaceOne
from dataclasses import asdict
import logging
from pymongo.errors import BulkWriteError

logger = logging.getLogger(__name__)

class MongoRecipeRepository(RecipeDocumentRepository):
    """Реалізує RecipeDocumentRepository.

    upsert_many: bulk_write із ReplaceOne(upsert=True) і ordered=False —
    при ordered=False помилка одного документа не зупиняє запис решти,
    а mongos може паралельно відправляти частини пачки на різні шарди.
    """

    def __init__(self, client: AsyncMongoClient, db_name: str) -> None:
        self._collection = client[db_name]["recipes"]

    async def upsert_many(self, recipes: list[Recipe]) -> int:
        if not recipes:
            return 0
        operations = []
        for recipe in recipes:
            doc = asdict(recipe)
            doc["_id"] = doc.pop("id")
            op = ReplaceOne(filter = {"_id": doc["_id"]},
                            replacement = doc,
                            upsert = True)
            operations.append(op)
        
        try:
            result = await self._collection.bulk_write(operations, ordered = False)
            return result.upserted_count + result.matched_count
        except BulkWriteError as e:
            logger.error("Entry error: %s", e)
            return len(recipes) - len(e.details["writeErrors"])

    async def delete(self, recipe_id: str) -> bool:
        result = await self._collection.delete_one({"_id": recipe_id})
        return result.deleted_count > 0


class MongoChefRepository(ChefRepository):
    """Реалізує ChefRepository. Колекція chefs невелика і не шардується."""

    def __init__(self, client: AsyncMongoClient, db_name: str) -> None:
        self._collection = client[db_name]["chefs"]

    async def upsert_many(self, chefs: list[Chef]) -> int:
        if not chefs:
            return 0
        operations = []
        for chef in chefs:
            doc = asdict(chef)
            doc["_id"] = doc.pop("id")
            op = ReplaceOne(filter = {"_id": doc["_id"]},
                                        replacement = doc,
                                        upsert = True)
            operations.append(op)
        try:
            result = await self._collection.bulk_write(operations, ordered = False)
            return result.upserted_count + result.matched_count
        except BulkWriteError as e:
            logger.error("Entry error: %s", e)
            return len(chefs) - len(e.details["writeErrors"])