import argparse
import asyncio
import random

from pymongo import AsyncMongoClient

from ingest_service.adapters.outbound.csv_recipe_source import CsvRecipeSource
from ingest_service.domain.cuisines import CUISINES
from ingest_service.domain.raw_recipe import RawRecipe
from writer_service.adapters.outbound.mongo_repositories import (
    MongoChefRepository,
    MongoRecipeRepository,
)
from writer_service.domain.chef import Chef
from writer_service.domain.recipe import Recipe

CSV_PATH = "data/RAW_recipes.csv"
BATCH_SIZE = 500
RECIPES_TO_LOAD = 10000


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest recipes from a CSV file.")
    parser.add_argument(
        "--limit",
        type=int,
        default=RECIPES_TO_LOAD,
        help="max number of recipes to ingest (default: %(default)s)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=BATCH_SIZE,
        help="recipes per batch (default: %(default)s)",
    )
    parser.add_argument(
        "--csv-path", default=CSV_PATH, help="path to the CSV file (default: %(default)s)"
    )
    parser.add_argument(
        "--mongo-url",
        default="mongodb://localhost:27017",
        help="MongoDB connection URL (default: %(default)s)",
    )
    return parser.parse_args()


def clear_batch(batch: list[RawRecipe]) -> list[Recipe]:
    return [
        Recipe(
            id=f"r-{recipe.source_id}",
            title=recipe.title,
            chef_id=f"c-{recipe.chef_id}",
            cuisine=pick_cuisine(recipe.tags) if recipe.tags is not None else None,
            cook_time_min=recipe.cook_time_min
            if recipe.cook_time_min is not None
            and recipe.cook_time_min <= 10080
            and recipe.cook_time_min >= 1
            else None,
            calories=recipe.calories
            if recipe.calories is not None and recipe.calories <= 20000 and recipe.calories >= 0
            else None,
            tags=recipe.tags if recipe.tags is not None else [],
            ingredients=recipe.ingredients if recipe.ingredients is not None else [],
            steps=recipe.steps if recipe.steps is not None else [],
            description=recipe.description if recipe.description is not None else "",
        )
        for recipe in batch
    ]


def pick_cuisine(tags: list[str]) -> str | None:
    for tag in tags:
        if tag in CUISINES:
            return tag
    return None


def generate_chef(chef_id, names: list[str], lastnames: list[str]) -> Chef:
    rng = random.Random(chef_id)
    return Chef(
        id=f"c-{chef_id}",
        full_name=f"{rng.choice(names)} {rng.choice(lastnames)}",
    )


async def main() -> None:
    args = parse_args()

    names = ["name1", "name2", "name3"]
    lastnames = ["lastname1", "lastname2", "lastname3"]

    source = CsvRecipeSource(args.csv_path)
    client = AsyncMongoClient(args.mongo_url)
    recipe_repo = MongoRecipeRepository(client=client, db_name="recipes")
    chef_repo = MongoChefRepository(client=client, db_name="recipes")

    for _ in range(0, args.limit, args.batch_size):
        batch = await source.next_batch(args.batch_size)
        recipes = clear_batch(batch)
        print(f"Loaded {len(recipes)} recipes from {args.csv_path}")
        await recipe_repo.upsert_many(recipes)
        print(f"Upserted {len(recipes)} recipes to recipes MongoDB")
        await chef_repo.upsert_many(
            [generate_chef(raw_recipe.chef_id, names, lastnames) for raw_recipe in batch]
        )
        print(f"Upserted {len(batch)} chefs to chefs MongoDB")


if __name__ == "__main__":
    asyncio.run(main())
