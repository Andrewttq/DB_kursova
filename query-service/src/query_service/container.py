"""Збирання залежностей query-service (Dependency Injection вручну).

Порядок «зовні всередину»:
    клієнти БД -> вихідні адаптери -> сервіси -> фасади -> контролери.
Контролери отримують фасади як ІНТЕРФЕЙСИ (вхідні порти), сервіси отримують
адаптери як ІНТЕРФЕЙСИ (вихідні порти). Тільки цей файл знає конкретні класи.
"""

from dataclasses import dataclass
from pathlib import Path

import httpx
from elasticsearch import AsyncElasticsearch
from fastapi import APIRouter
from fastapi.templating import Jinja2Templates
from neo4j import AsyncDriver, AsyncGraphDatabase
from pymongo import AsyncMongoClient
from redis.asyncio import Redis

from query_service.adapters.inbound.chef_controller import ChefController
from query_service.adapters.inbound.monitoring_controller import MonitoringController
from query_service.adapters.inbound.recipe_controller import RecipeController
from query_service.adapters.inbound.search_controller import SearchController
from query_service.adapters.inbound.ui_controller import UiController
from query_service.adapters.outbound.elastic_repositories import ElasticRecipeSearchRepository
from query_service.adapters.outbound.mongo_repositories import (
    MongoChefReadRepository,
    MongoRecipeReadRepository,
)
from query_service.adapters.outbound.neo4j_repositories import Neo4jRecipeGraphReadRepository
from query_service.adapters.outbound.rabbit_metrics import RabbitQueueMetricsAdapter
from query_service.adapters.outbound.redis_repositories import (
    RedisIngestConfigRepository,
    RedisSearchCache,
    RedisSearchLogRepository,
    RedisStatsReadRepository,
)
from query_service.application.facades.chef_query_facade import ChefQueryFacade
from query_service.application.facades.monitoring_facade import MonitoringFacade
from query_service.application.facades.recipe_query_facade import RecipeQueryFacade
from query_service.application.facades.search_facade import SearchFacade
from query_service.application.services.chef_service import ChefService
from query_service.application.services.monitoring_services import (
    GeneratorControlService,
    StatsService,
)
from query_service.application.services.recipe_services import (
    RecipeInformationService,
    RecipeRelationService,
)
from query_service.application.services.search_services import (
    QueryNormalizer,
    RecipeSearchService,
    SearchCacheService,
    SearchLogService,
)
from query_service.settings import Settings

TEMPLATES_DIR = Path(__file__).parent / "templates"


@dataclass
class Container:
    mongo: AsyncMongoClient
    es: AsyncElasticsearch
    neo4j: AsyncDriver
    redis: Redis
    http: httpx.AsyncClient
    routers: list[APIRouter]

    async def close(self) -> None:
        await self.mongo.close()
        await self.es.close()
        await self.neo4j.close()
        await self.redis.aclose()
        await self.http.aclose()


def build_container(settings: Settings) -> Container:
    # 1. Клієнти
    mongo = AsyncMongoClient(settings.mongo_url)
    es = AsyncElasticsearch(settings.es_url)
    neo4j = AsyncGraphDatabase.driver(
        settings.neo4j_url, auth=(settings.neo4j_user, settings.neo4j_password)
    )
    redis = Redis.from_url(settings.redis_url)
    http = httpx.AsyncClient(auth=("guest", "guest"), timeout=2.0)
    templates = Jinja2Templates(directory=TEMPLATES_DIR)

    # 2. Сервіси з вихідними адаптерами
    recipes = RecipeInformationService(MongoRecipeReadRepository(mongo, settings.mongo_db))
    relations = RecipeRelationService(Neo4jRecipeGraphReadRepository(neo4j))
    chefs = ChefService(MongoChefReadRepository(mongo, settings.mongo_db))
    search_log = SearchLogService(RedisSearchLogRepository(redis))
    stats = StatsService(
        RedisStatsReadRepository(redis),
        RabbitQueueMetricsAdapter(http, settings.rabbit_management_url, settings.rabbit_queue),
    )
    generator = GeneratorControlService(
        RedisIngestConfigRepository(redis), settings.ingest_default_rate
    )

    # 3. Фасади (реалізації вхідних портів)
    recipe_facade = RecipeQueryFacade(recipes=recipes, chefs=chefs, relations=relations)
    chef_facade = ChefQueryFacade(chefs=chefs, relations=relations, recipes=recipes)
    search_facade = SearchFacade(
        normalizer=QueryNormalizer(),
        cache=SearchCacheService(RedisSearchCache(redis), settings.search_cache_ttl_sec),
        search=RecipeSearchService(ElasticRecipeSearchRepository(es, settings.es_index)),
        log=search_log,
    )
    monitoring_facade = MonitoringFacade(stats=stats, search_log=search_log, generator=generator)

    # 4. Контролери (вхідні адаптери)
    routers = [
        RecipeController(recipe_facade).router,
        ChefController(chef_facade).router,
        SearchController(search_facade, templates).router,
        MonitoringController(monitoring_facade, monitoring_facade, templates).router,
        UiController(templates).router,
    ]
    return Container(mongo=mongo, es=es, neo4j=neo4j, redis=redis, http=http, routers=routers)
