"""Вихідний адаптер Elasticsearch для пошуку."""

from elasticsearch import AsyncElasticsearch, NotFoundError

from query_service.application.ports.outbound.search_ports import RecipeSearchRepository
from query_service.domain.search import SearchHit

# Порядок, у якому шукаємо фрагмент для сніпета: опис найзрозуміліший користувачу.
_SNIPPET_FIELDS = ("description", "steps", "ingredients", "title")


class ElasticRecipeSearchRepository(RecipeSearchRepository):
    """Реалізує RecipeSearchRepository.

    Запит: bool-запит
        must   — multi_match по title^3, ingredients^2, description, steps
                 (^3 — збіг у назві втричі важливіший за збіг в описі);
                 fuzziness AUTO — знаходить слова з однією-двома помилками (chiken -> chicken);
        filter — term по cuisine, range по cook_time_min і calories (фільтри не впливають
                 на score і кешуються самим Elasticsearch).
    Рецепти без часу чи калорійності (None) у відповідний range-фільтр не потрапляють.
    Посторінкове виведення: from = (page - 1) * size.
    highlight -> SearchHit.snippet з тегами <em>. encoder=html екранує HTML у тексті рецепта,
    тому на сторінці виконається лише наш <em>, а не чужий код.
    """

    def __init__(self, client: AsyncElasticsearch, index_name: str) -> None:
        self._client = client
        self._index_name = index_name

    @staticmethod
    def build_query(
        text: str,
        cuisine: str | None,
        max_cook_time_min: int | None,
        max_calories: float | None,
    ) -> dict:
        filters: list[dict] = []
        if cuisine:
            filters.append({"term": {"cuisine": cuisine}})
        if max_cook_time_min is not None:
            filters.append({"range": {"cook_time_min": {"lte": max_cook_time_min}}})
        if max_calories is not None:
            filters.append({"range": {"calories": {"lte": max_calories}}})
        return {
            "bool": {
                "must": [
                    {
                        "multi_match": {
                            "query": text,
                            "fields": ["title^3", "ingredients^2", "description", "steps"],
                            "fuzziness": "AUTO",
                            # з трьох слів запиту мають збігтися хоча б два
                            "minimum_should_match": "2<75%",
                        }
                    }
                ],
                "filter": filters,
            }
        }

    async def search(
        self,
        text: str,
        cuisine: str | None,
        max_cook_time_min: int | None,
        max_calories: float | None,
        page: int,
        size: int,
    ) -> list[SearchHit]:
        try:
            response = await self._client.search(
                index=self._index_name,
                query=self.build_query(text, cuisine, max_cook_time_min, max_calories),
                from_=(page - 1) * size,
                size=size,
                source_includes=["title"],
                highlight={
                    "encoder": "html",
                    "pre_tags": ["<em>"],
                    "post_tags": ["</em>"],
                    "fields": {f: {} for f in _SNIPPET_FIELDS},
                    "fragment_size": 150,
                    "number_of_fragments": 1,
                },
            )
        except NotFoundError:
            # Індексу ще немає (writer-service з роллю es не запускався) — це порожній результат.
            return []
        return [self._to_hit(h) for h in response["hits"]["hits"]]

    @staticmethod
    def _to_hit(h: dict) -> SearchHit:
        highlight = h.get("highlight", {})
        snippet = next((highlight[f][0] for f in _SNIPPET_FIELDS if f in highlight), "")
        return SearchHit(
            recipe_id=h["_id"],
            title=h["_source"].get("title", h["_id"]),
            snippet=snippet,
            score=h["_score"] or 0.0,
        )
