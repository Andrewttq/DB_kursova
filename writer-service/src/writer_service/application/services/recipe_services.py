"""Прикладні сервіси для рецептів.

Кожен сервіс відповідає за один тип сховища і працює лише через свій порт.
Фасад (RecipeCommandFacade) поєднує їх в одну бізнес-операцію.
Таке розділення дає змогу, наприклад, тимчасово вимкнути Neo4j,
не чіпаючи логіку запису в Mongo та Elasticsearch.
"""

from writer_service.application.ports.outbound.recipe_repositories import (
    RecipeDocumentRepository,
    RecipeGraphRepository,
    RecipeSearchIndexRepository,
)
from writer_service.domain.recipe import Recipe


def _dedupe(recipes: list[Recipe]) -> list[Recipe]:
    """Якщо той самий рецепт двічі потрапив у пачку (повторна доставка),
    залишаємо останню версію: upsert однаково дасть той самий результат."""
    return list({r.id: r for r in recipes}.values())


class RecipeInformationService:
    """Картки рецептів у MongoDB."""

    def __init__(self, repository: RecipeDocumentRepository) -> None:
        self._repository = repository

    async def save_many(self, recipes: list[Recipe]) -> int:
        return await self._repository.upsert_many(_dedupe(recipes))


class RecipeRelationService:
    """Граф зв'язків у Neo4j."""

    def __init__(self, graph: RecipeGraphRepository) -> None:
        self._graph = graph

    async def register_many(self, recipes: list[Recipe]) -> int:
        return await self._graph.merge_many(_dedupe(recipes))


class RecipeIndexService:
    """Повнотекстовий індекс в Elasticsearch."""

    def __init__(self, index: RecipeSearchIndexRepository) -> None:
        self._index = index

    async def index_many(self, recipes: list[Recipe]) -> int:
        return await self._index.index_many(_dedupe(recipes))
