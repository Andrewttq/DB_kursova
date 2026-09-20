"""Вихідні адаптери MongoDB для читання (асинхронний PyMongo)."""

from pymongo import AsyncMongoClient

from query_service.application.ports.outbound.chef_repositories import ChefReadRepository
from query_service.application.ports.outbound.recipe_repositories import RecipeReadRepository
from query_service.domain.chef import Chef
from query_service.domain.recipe import Recipe


class MongoRecipeReadRepository(RecipeReadRepository):
    """Реалізує RecipeReadRepository.

    find_by_id — адресний (targeted) запит: mongos обчислює хеш _id
    і звертається лише до одного шарда.
    find_by_filter — запит до всіх шардів (scatter-gather), тому потрібен
    індекс { cuisine: 1, cook_time_min: 1 }. Перевірити план: .explain().
    """

    def __init__(self, client: AsyncMongoClient, db_name: str) -> None:
        self._collection = client[db_name]["recipes"]

    async def find_by_id(self, recipe_id: str) -> Recipe | None:
        raise NotImplementedError

    async def find_by_ids(self, recipe_ids: list[str]) -> list[Recipe]:
        raise NotImplementedError

    async def find_by_filter(
        self,
        cuisine: str | None,
        max_cook_time_min: int | None,
        max_calories: float | None,
        skip: int,
        limit: int,
    ) -> list[Recipe]:
        raise NotImplementedError


class MongoChefReadRepository(ChefReadRepository):
    def __init__(self, client: AsyncMongoClient, db_name: str) -> None:
        self._collection = client[db_name]["chefs"]

    async def find_by_id(self, chef_id: str) -> Chef | None:
        raise NotImplementedError
