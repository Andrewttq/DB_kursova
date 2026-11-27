"""Фасад — реалізація SearchRecipesUseCase.

Алгоритм пошуку:
    1. QueryNormalizer.cache_key(...)          — нормалізований ключ;
    2. SearchCacheService.get(key)             — Redis; якщо є, повернути (from_cache=True);
    3. RecipeSearchService.search(...)         — Elasticsearch, якщо в кеші немає;
    4. SearchCacheService.put(key, hits)       — покласти результат у кеш;
    5. SearchLogService.log(...)               — записати запит у журнал;
    6. mappers -> SearchResponseDTO з часом виконання (took_ms).
"""

import logging
import time

from query_service.application import mappers
from query_service.application.dto import SearchLogDTO, SearchRequestDTO, SearchResponseDTO
from query_service.application.ports.inbound.search_use_case import SearchRecipesUseCase
from query_service.application.services.search_services import (
    QueryNormalizer,
    RecipeSearchService,
    SearchCacheService,
    SearchLogService,
)
from query_service.domain.search import SearchLogEntry

logger = logging.getLogger(__name__)


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
        started = time.perf_counter()
        filters = {
            "cuisine": request.cuisine,
            "max_cook_time_min": request.max_cook_time_min,
            "max_calories": request.max_calories,
        }
        key = self._normalizer.cache_key(request.query, filters, request.page, request.size)

        hits = await self._cache.get(key)
        from_cache = hits is not None
        if hits is None:
            es_started = time.perf_counter()
            hits = await self._search.search(
                request.query,
                request.cuisine,
                request.max_cook_time_min,
                request.max_calories,
                request.page,
                request.size,
            )
            logger.debug("Elasticsearch: %.1f мс", (time.perf_counter() - es_started) * 1000)
            await self._cache.put(key, hits)

        took_ms = (time.perf_counter() - started) * 1000
        await self._log.log(
            SearchLogEntry(
                raw_query=request.query,
                normalized_key=key,
                hits_count=len(hits),
                from_cache=from_cache,
                took_ms=round(took_ms, 2),
            )
        )
        logger.info(
            "Пошук %r: %d результатів, з кешу=%s, %.1f мс",
            request.query,
            len(hits),
            from_cache,
            took_ms,
        )
        return SearchResponseDTO(
            query=request.query,
            normalized_key=key,
            from_cache=from_cache,
            took_ms=round(took_ms, 2),
            hits=[mappers.hit_to_dto(h) for h in hits],
        )

    async def recent_searches(self, limit: int) -> list[SearchLogDTO]:
        entries = await self._log.recent(limit)
        return [mappers.log_entry_to_dto(e) for e in entries]
