"""Вихідний адаптер Elasticsearch для пошуку."""

from elasticsearch import AsyncElasticsearch

from query_service.application.ports.outbound.search_ports import RecipeSearchRepository
from query_service.domain.search import SearchHit


class ElasticRecipeSearchRepository(RecipeSearchRepository):
    """Реалізує RecipeSearchRepository.

    Запит: bool-запит
        must   — multi_match по title^3, description, steps, ingredients
                 (^3 — назва важливіша за інші поля);
        filter — term по cuisine, range по cook_time_min (фільтри не впливають на score
                 і кешуються самим Elasticsearch).
    highlight по description і steps -> SearchHit.snippet з тегами <em>.
    """

    def __init__(self, client: AsyncElasticsearch, index_name: str) -> None:
        self._client = client
        self._index_name = index_name

    async def search(
        self, text: str, cuisine: str | None, max_cook_time_min: int | None, size: int
    ) -> list[SearchHit]:
        raise NotImplementedError
