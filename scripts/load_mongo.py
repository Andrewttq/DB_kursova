import argparse
import asyncio

from pymongo import AsyncMongoClient

from ingest_service.adapters.outbound.csv_recipe_source import CsvRecipeSource
from ingest_service.util import clear_batch, generate_chef
from writer_service.adapters.outbound.mongo_repositories import (
    MongoChefRepository,
    MongoRecipeRepository,
)

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
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    names = ["name1", "name2", "name3"]
    lastnames = ["lastname1", "lastname2", "lastname3"]

    source = CsvRecipeSource(args.csv_path)
    client = AsyncMongoClient("mongodb://localhost:27017")
    recipe_repo = MongoRecipeRepository(client=client, db_name="recipes")
    chef_repo = MongoChefRepository(client=client, db_name="chefs")

    for _ in range(0, args.limit, args.batch_size):
        batch = asyncio.run(source.next_batch(args.batch_size))
        recipes = clear_batch(batch)
        print(f"Loaded {len(recipes)} recipes from {args.csv_path}")
        asyncio.run(recipe_repo.upsert_many(recipes))
        print(f"Upserted {len(recipes)} recipes to recipes MongoDB")
        asyncio.run(
            chef_repo.upsert_many(
                [generate_chef(recipe.chef_id, names, lastnames) for recipe in recipes]
            )
        )
        print(f"Upserted {len(recipes)} chefs to chefs MongoDB")


if __name__ == "__main__":
    main()
