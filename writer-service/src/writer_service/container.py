"""Збирання залежностей writer-service (Dependency Injection вручну).

Порядок збирання — «зовні всередину»:
    клієнти БД -> вихідні адаптери -> сервіси -> фасад -> вхідний адаптер.
Жоден клас прикладного шару не створює адаптери сам, усе передається тут.
Створення клієнтів не відкриває з'єднань одразу — вони встановлюються при першому запиті.
"""

from dataclasses import dataclass

from elasticsearch import AsyncElasticsearch
from neo4j import AsyncDriver, AsyncGraphDatabase
from pymongo import AsyncMongoClient
from redis.asyncio import Redis

from writer_service.adapters.inbound.rabbit_recipe_consumer import RabbitRecipeConsumer
from writer_service.adapters.outbound.elastic_repositories import ElasticRecipeIndexRepository
from writer_service.adapters.outbound.mongo_repositories import (
    MongoChefRepository,
    MongoRecipeRepository,
)
from writer_service.adapters.outbound.neo4j_repositories import Neo4jRecipeGraphRepository
from writer_service.adapters.outbound.redis_repositories import RedisWriteStatsRepository
from writer_service.application.facades.recipe_command_facade import RecipeCommandFacade
from writer_service.application.services.chef_service import ChefService
from writer_service.application.services.recipe_services import (
    RecipeIndexService,
    RecipeInformationService,
    RecipeRelationService,
)
from writer_service.application.services.write_stats_service import WriteStatsService
from writer_service.settings import Settings


@dataclass
class Container:
    mongo: AsyncMongoClient
    es: AsyncElasticsearch
    neo4j: AsyncDriver
    redis: Redis
    es_index: ElasticRecipeIndexRepository
    consumer: RabbitRecipeConsumer

    async def close(self) -> None:
        """Закрити всі клієнти БД при зупинці сервісу."""
        await self.mongo.close()
        await self.es.close()
        await self.neo4j.close()
        await self.redis.aclose()


def build_container(settings: Settings) -> Container:
    # 1. Клієнти баз даних
    mongo = AsyncMongoClient(settings.mongo_url)
    es = AsyncElasticsearch(settings.es_url)
    neo4j = AsyncGraphDatabase.driver(
        settings.neo4j_url, auth=(settings.neo4j_user, settings.neo4j_password)
    )
    redis = Redis.from_url(settings.redis_url)

    # 2. Вихідні адаптери (реалізації портів)
    recipe_repo = MongoRecipeRepository(mongo, settings.mongo_db)
    chef_repo = MongoChefRepository(mongo, settings.mongo_db)
    graph_repo = Neo4jRecipeGraphRepository(neo4j)
    es_index = ElasticRecipeIndexRepository(es, settings.es_index)
    stats_repo = RedisWriteStatsRepository(redis)

    # 3. Прикладні сервіси та фасад
    facade = RecipeCommandFacade(
        recipes=RecipeInformationService(recipe_repo),
        chefs=ChefService(chef_repo),
        relations=RecipeRelationService(graph_repo),
        index=RecipeIndexService(es_index),
        stats=WriteStatsService(stats_repo),
    )

    # 4. Вхідний адаптер
    consumer = RabbitRecipeConsumer(
        use_case=facade,
        rabbit_url=settings.rabbit_url,
        queue_name=settings.rabbit_queue,
        batch_size=settings.writer_batch_size,
        batch_timeout_ms=settings.writer_batch_timeout_ms,
        prefetch_count=settings.writer_prefetch_count,
    )
    return Container(
        mongo=mongo, es=es, neo4j=neo4j, redis=redis, es_index=es_index, consumer=consumer
    )
