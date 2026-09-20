"""Фасад — реалізація SearchRecipesUseCase.

Алгоритм пошуку:
    1. QueryNormalizer.cache_key(...)          — нормалізований ключ;
    2. SearchCacheService.get(key)             — Redis; якщо є, повернути (from_cache=True);
    3. RecipeSearchService.search(...)         — Elasticsearch, якщо в кеші немає;
    4. SearchCacheService.put(key, hits)       — покласти результат у кеш;
    5. SearchLogService.log(...)               — записати запит у журнал;
    6. mappers -> SearchResponseDTO з часом виконання (took_ms).
"""

from query_service.application.dto import SearchRequestDTO, SearchResponseDTO
from query_service.application.ports.inbound.search_use_case import SearchRecipesUseCase
from query_service.application.services.search_services import (
    QueryNormalizer,
    RecipeSearchService,
    SearchCacheService,
    SearchLogService,
)


class SearchFacade(SearchRecipesUseCase):
    def __init__(
        self,
        normalizer: QueryNormalizer,
        cache: SearchCacheService,
        search: RecipeSearchService,
        log: SearchLogService,
    ) -> None:
        self._normalizer = normalizer
        self._cache = cache
        self._search = search
        self._log = log

    async def search(self, request: SearchRequestDTO) -> SearchResponseDTO:
        raise NotImplementedError
