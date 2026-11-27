"""Швидке завантаження рецептів з CSV одразу в MongoDB (без RabbitMQ).

Потрібне, щоб наповнити базу для демонстрації сторінок і аналітики, коли повний
конвеєр (ingest -> RabbitMQ -> writer) не запущено. Використовує ті самі правила
очищення (ingest_service.domain.cleaning) і ті самі імена шефів (writer_service.mappers),
тому дані виходять ідентичні тим, що записав би конвеєр.

Запуск:
    uv run python scripts/load_mongo.py --limit 20000
    uv run python scripts/load_mongo.py --mongo-url mongodb://localhost:27018   (шарди)
Після цього можна наповнити пошук і граф: scripts/reindex_from_mongo.py --es --neo4j
"""

import argparse
import asyncio

from pymongo import AsyncMongoClient

from ingest_service.adapters.outbound.csv_recipe_source import CsvRecipeSource
from ingest_service.domain import cleaning
from ingest_service.domain.raw_recipe import RawRecipe
from writer_service.adapters.outbound.mongo_repositories import (
    MongoChefRepository,
    MongoRecipeRepository,
)
from writer_service.application.mappers import chef_name
from writer_service.domain.chef import Chef
from writer_service.domain.recipe import Recipe


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Завантажити рецепти з CSV у MongoDB")
    parser.add_argument("--limit", type=int, default=10_000, help="скільки рецептів (%(default)s)")
    parser.add_argument("--batch-size", type=int, default=500, help="розмір пачки (%(default)s)")
    parser.add_argument("--csv-path", default="data/RAW_recipes.csv")
    parser.add_argument("--mongo-url", default="mongodb://localhost:27017")
    return parser.parse_args()


def to_recipe(raw: RawRecipe) -> Recipe:
    return Recipe(
        id=cleaning.recipe_id(raw.source_id),
        title=raw.title,
        chef_id=cleaning.chef_id(raw.chef_id),
        cuisine=cleaning.pick_cuisine(raw.tags),
        cook_time_min=cleaning.clean_cook_time(raw.cook_time_min),
        calories=cleaning.clean_calories(raw.calories),
        tags=raw.tags,
        ingredients=raw.ingredients,
        steps=raw.steps,
        description=raw.description or "",
    )


def to_chef(raw: RawRecipe) -> Chef:
    cid = cleaning.chef_id(raw.chef_id)
    return Chef(id=cid, full_name=chef_name(cid))


async def main() -> None:
    args = parse_args()
    source = CsvRecipeSource(args.csv_path)
    client = AsyncMongoClient(args.mongo_url)
    recipes = MongoRecipeRepository(client=client, db_name="recipes")
    chefs = MongoChefRepository(client=client, db_name="recipes")

    loaded = 0
    while loaded < args.limit:
        batch = await source.next_batch(min(args.batch_size, args.limit - loaded))
        if not batch:
            break
        await recipes.upsert_many([to_recipe(r) for r in batch])
        await chefs.upsert_many(list({c.id: c for c in map(to_chef, batch)}.values()))
        loaded += len(batch)
        print(f"\rЗавантажено: {loaded}", end="", flush=True)
        if len(batch) < args.batch_size:
            break  # файл закінчився
    print(f"\nГотово: {loaded} рецептів у {args.mongo_url}")
    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
