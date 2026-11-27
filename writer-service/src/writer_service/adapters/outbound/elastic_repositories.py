"""Вихідний адаптер Elasticsearch (AsyncElasticsearch)."""

import logging
from dataclasses import asdict

from elasticsearch import AsyncElasticsearch, NotFoundError
from elasticsearch.helpers import async_bulk

from writer_service.application.ports.outbound.recipe_repositories import (
    RecipeSearchIndexRepository,
)
from writer_service.domain.recipe import Recipe

logger = logging.getLogger(__name__)

# Схема індексу (див. також docs/CONTRACTS.md).
#   text + analyzer english — розбивається на слова, приводиться до нижнього регістру,
#                             закінчення відкидаються (chickens -> chicken): по цих полях шукають;
#   keyword                 — зберігається як є: по цих полях фільтрують точним збігом;
#   integer / float         — для фільтрів за діапазоном (range).
RECIPES_MAPPING = {
    "properties": {
        "title": {"type": "text", "analyzer": "english"},
        "description": {"type": "text", "analyzer": "english"},
        "steps": {"type": "text", "analyzer": "english"},
        "ingredients": {"type": "text", "analyzer": "english"},
        "cuisine": {"type": "keyword"},
        "tags": {"type": "keyword"},
        "chef_id": {"type": "keyword"},
        "cook_time_min": {"type": "integer"},
        "calories": {"type": "float"},
    }
}


class ElasticRecipeIndexRepository(RecipeSearchIndexRepository):
    """Реалізує RecipeSearchIndexRepository.

    index_many — через helpers.async_bulk, id документа = id рецепта
    (повторна індексація просто перезапише документ — ідемпотентність).
    Mapping індексу створюється один раз при старті (ensure_index).
    """

    def __init__(self, client: AsyncElasticsearch, index_name: str) -> None:
        self._client = client
        self._index_name = index_name

    async def ensure_index(self) -> None:
        """Створити індекс із mapping, якщо його ще немає."""
        if await self._client.indices.exists(index=self._index_name):
            return
        await self._client.indices.create(index=self._index_name, mappings=RECIPES_MAPPING)
        logger.info("Створено індекс Elasticsearch %s", self._index_name)

    def _actions(self, recipes: list[Recipe]):
        for recipe in recipes:
            doc = asdict(recipe)
            doc_id = doc.pop("id")
            yield {"_index": self._index_name, "_id": doc_id, "_source": doc}

    async def index_many(self, recipes: list[Recipe]) -> int:
        if not recipes:
            return 0
        # raise_on_error=False: одна погана пачка не зупиняє запис решти документів
        success, errors = await async_bulk(
            self._client, self._actions(recipes), raise_on_error=False, chunk_size=1000
        )
        if errors:
            logger.error("Elasticsearch не прийняв %d документів: %s", len(errors), errors[:1])
        return success

    async def delete(self, recipe_id: str) -> None:
        try:
            await self._client.delete(index=self._index_name, id=recipe_id)
        except NotFoundError:
            pass  # документа вже немає — результат той самий
