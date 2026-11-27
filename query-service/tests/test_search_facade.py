"""Тести алгоритму пошуку з кешем (cache-aside) без Redis і Elasticsearch."""

from query_fakes import FakeCache, FakeLog, FakeSearch

from query_service.application.dto import SearchRequestDTO
from query_service.application.facades.search_facade import SearchFacade
from query_service.application.services.search_services import (
    QueryNormalizer,
    RecipeSearchService,
    SearchCacheService,
    SearchLogService,
)
from query_service.domain.search import SearchHit

HITS = [
    SearchHit("r1", "Garlic chicken pasta", "with <em>garlic</em>", 3.2),
    SearchHit("r2", "Borscht", "beet soup", 1.0),
]


def make(cache_enabled: bool = True):
    search, cache, log = FakeSearch(HITS), FakeCache(), FakeLog()
    facade = SearchFacade(
        normalizer=QueryNormalizer(),
        cache=SearchCacheService(cache, ttl_sec=300, enabled=cache_enabled),
        search=RecipeSearchService(search),
        log=SearchLogService(log),
    )
    return facade, search, log


async def test_second_identical_query_comes_from_cache():
    facade, search, _ = make()
    first = await facade.search(SearchRequestDTO(query="garlic chicken"))
    second = await facade.search(SearchRequestDTO(query="Chicken, GARLIC"))
    assert first.from_cache is False
    assert second.from_cache is True
    assert search.calls == 1  # Elasticsearch викликано лише один раз
    assert [h.recipe_id for h in second.hits] == ["r1"]


async def test_empty_result_is_cached_and_logged_as_empty():
    facade, search, log = make()
    await facade.search(SearchRequestDTO(query="zzzz"))
    again = await facade.search(SearchRequestDTO(query="zzzz"))
    assert again.hits == [] and again.from_cache is True
    assert search.calls == 1
    recent = await facade.recent_searches(5)
    assert recent[0].status == "Пусто"


async def test_cache_can_be_disabled():
    facade, search, _ = make(cache_enabled=False)
    await facade.search(SearchRequestDTO(query="borscht"))
    second = await facade.search(SearchRequestDTO(query="borscht"))
    assert second.from_cache is False
    assert search.calls == 2


async def test_every_search_is_logged():
    facade, _, log = make()
    await facade.search(SearchRequestDTO(query="pasta"))
    await facade.search(SearchRequestDTO(query="pasta"))
    assert [e.from_cache for e in log.entries] == [True, False]


async def test_search_works_when_redis_is_down():
    class DownCache(FakeCache):
        async def get(self, key):
            raise ConnectionError("redis down")

        async def put(self, key, hits, ttl_sec):
            raise ConnectionError("redis down")

    class DownLog(FakeLog):
        async def append(self, entry):
            raise ConnectionError("redis down")

    facade = SearchFacade(
        normalizer=QueryNormalizer(),
        cache=SearchCacheService(DownCache(), ttl_sec=300),
        search=RecipeSearchService(FakeSearch(HITS)),
        log=SearchLogService(DownLog()),
    )
    result = await facade.search(SearchRequestDTO(query="garlic"))
    assert [h.recipe_id for h in result.hits] == ["r1"]
    assert result.from_cache is False
