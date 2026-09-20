"""Вихідний адаптер Elasticsearch (AsyncElasticsearch)."""

from elasticsearch import AsyncElasticsearch

from writer_service.application.ports.outbound.recipe_repositories import (
    RecipeSearchIndexRepository,
)
from writer_service.domain.recipe import Recipe


class ElasticRecipeIndexRepository(RecipeSearchIndexRepository):
    """Реалізує RecipeSearchIndexRepository.

    index_many — через helpers.async_bulk, id документа = id рецепта
    (повторна індексація просто перезапише документ).
    Mapping індексу (створюється один раз при старті):
        title, description, steps, ingredients — text (аналізатор english);
        cuisine, tags                          — keyword (для фільтрів);
        cook_time_min, calories                — числа (для фільтрів).
    """

    def __init__(self, client: AsyncElasticsearch, index_name: str) -> None:
        self._client = client
        self._index_name = index_name

    async def ensure_index(self) -> None:
        """Створити індекс із mapping, якщо його ще немає."""
        raise NotImplementedError

    async def index_many(self, recipes: list[Recipe]) -> int:
        raise NotImplementedError

    async def delete(self, recipe_id: str) -> None:
        raise NotImplementedError
