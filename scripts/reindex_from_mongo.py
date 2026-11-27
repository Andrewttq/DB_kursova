"""Перебудувати індекс Elasticsearch і/або граф Neo4j з MongoDB.

MongoDB — джерело істини, ES і Neo4j — похідні сховища. Якщо індекс чи граф
зіпсувалися або дані завантажено лише в Mongo (scripts/load_mongo.py), їх можна
відновити цим скриптом без повторного проходу через RabbitMQ.
Використовує ті самі адаптери writer-service, що й робочий запис.

Запуск (бази підняті через docker compose up -d):
    uv run --package writer-service python scripts/reindex_from_mongo.py --es
    uv run --package writer-service python scripts/reindex_from_mongo.py --es --neo4j
    ... --mongo-url mongodb://localhost:27018      (шардований кластер через mongos)
"""

import argparse
import asyncio
import time
from dataclasses import fields

from elasticsearch import AsyncElasticsearch
from neo4j import AsyncGraphDatabase
from pymongo import AsyncMongoClient

from writer_service.adapters.outbound.elastic_repositories import ElasticRecipeIndexRepository
from writer_service.adapters.outbound.neo4j_repositories import Neo4jRecipeGraphRepository
from writer_service.domain.recipe import Recipe
from writer_service.settings import Settings

FIELDS = {f.name for f in fields(Recipe)}


def to_recipe(doc: dict) -> Recipe:
    doc = dict(doc)
    doc["id"] = doc.pop("_id")
    return Recipe(**{k: v for k, v in doc.items() if k in FIELDS})


async def main() -> None:
    settings = Settings()
    p = argparse.ArgumentParser(description="Перебудувати ES / Neo4j з MongoDB")
    p.add_argument("--es", action="store_true", help="перебудувати індекс Elasticsearch")
    p.add_argument("--neo4j", action="store_true", help="перебудувати граф Neo4j")
    p.add_argument("--mongo-url", default=settings.mongo_url)
    p.add_argument("--batch", type=int, default=1000)
    p.add_argument("--limit", type=int, default=0, help="0 — усі рецепти")
    args = p.parse_args()
    if not (args.es or args.neo4j):
        p.error("вкажіть --es та/або --neo4j")

    mongo = AsyncMongoClient(args.mongo_url)
    es = AsyncElasticsearch(settings.es_url)
    neo = AsyncGraphDatabase.driver(
        settings.neo4j_url, auth=(settings.neo4j_user, settings.neo4j_password)
    )
    index = ElasticRecipeIndexRepository(es, settings.es_index)
    graph = Neo4jRecipeGraphRepository(neo)
    if args.es:
        await index.ensure_index()
    if args.neo4j:
        await graph.ensure_schema()

    started, done = time.perf_counter(), 0
    cursor = mongo[settings.mongo_db]["recipes"].find({}, batch_size=args.batch)
    if args.limit:
        cursor = cursor.limit(args.limit)
    batch: list[Recipe] = []
    async for doc in cursor:
        batch.append(to_recipe(doc))
        if len(batch) >= args.batch:
            done += await flush(batch, index if args.es else None, graph if args.neo4j else None)
            print(f"\rОброблено: {done}", end="", flush=True)
            batch = []
    if batch:
        done += await flush(batch, index if args.es else None, graph if args.neo4j else None)
    if args.es:
        await es.indices.refresh(index=settings.es_index)
    print(f"\nГотово: {done} рецептів за {time.perf_counter() - started:.1f} с")

    await mongo.close()
    await es.close()
    await neo.close()


async def flush(batch, index, graph) -> int:
    if index is not None:
        await index.index_many(batch)
    if graph is not None:
        await graph.merge_many(batch)
    return len(batch)


if __name__ == "__main__":
    asyncio.run(main())
