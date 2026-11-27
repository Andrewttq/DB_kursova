"""Інтеграційні тести пошуку (вимога методички: позитивний і негативний).

Потребують запущених Elasticsearch і Redis (docker compose up -d), тому в CI
не запускаються. Локально: uv run pytest -m integration -v
"""

from uuid import uuid4

import pytest
from elasticsearch import AsyncElasticsearch
from httpx import ASGITransport, AsyncClient

from query_service.adapters.outbound.elastic_repositories import ElasticRecipeSearchRepository

pytestmark = pytest.mark.integration
ES_URL = "http://localhost:9200"


async def test_document_with_unique_marker_is_found_with_highlight():
    """Позитивний: документ з унікальним словом знаходиться, слово підсвічене."""
    es = AsyncElasticsearch(ES_URL)
    marker = f"marker{uuid4().hex}"
    doc_id = f"test-{marker}"
    await es.index(
        index="recipes",
        id=doc_id,
        refresh=True,  # документ доступний для пошуку одразу, без очікування ~1 с
        document={
            "title": "Integration test recipe",
            "description": f"secret word {marker}",
            "steps": [],
            "ingredients": [],
            "cuisine": "test",
            "tags": [],
            "cook_time_min": 1,
            "calories": 1.0,
        },
    )
    try:
        hits = await ElasticRecipeSearchRepository(es, "recipes").search(
            marker, None, None, None, 1, 10
        )
        assert [h.recipe_id for h in hits] == [doc_id]
        assert "<em>" in hits[0].snippet
    finally:
        await es.delete(index="recipes", id=doc_id, refresh=True)
        await es.close()


async def test_unknown_word_returns_empty_list_not_error():
    """Негативний: через увесь API (контролер -> фасад -> кеш -> ES) пустий результат —
    це 200 і порожній список, а не 500 і не випадкові дані."""
    from query_service.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/search", params={"q": f"nothing{uuid4().hex}"})
    assert response.status_code == 200
    assert response.json()["hits"] == []
