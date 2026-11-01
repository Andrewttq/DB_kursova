"""Демонстрація для завдання №6: запис і читання MongoDB."""
import asyncio
import logging

from pymongo import AsyncMongoClient

from writer_service.adapters.outbound.mongo_repositories import MongoRecipeRepository
from writer_service.domain.recipe import Recipe
from writer_service.main import setup_logging
from writer_service.settings import Settings

log = logging.getLogger(__name__).__name__
async def main() -> None:
    settings = Settings()
    setup_logging(settings.log_config)
    client = AsyncMongoClient(settings.mongo_url)
    repo = MongoRecipeRepository(client, settings.mongo_db)
    recipes = [
                Recipe(id="r-demo-1", title="Борщ", chef_id="chef-1", cuisine="Ukrainian"),
                Recipe(id="r-demo-2", title="Піца", chef_id="chef-2", cuisine="Italian")
              ]
    saved = await repo.upsert_many(recipes)
    log.info("Записано рецептів: %s", saved)
    doc = await client[settings.mongo_db]
    ["recipes"].find_one({"_id": "r-demo-1"})
    log.info("Прочитано з MongoDB: %s", doc)
    await client.close()
    if __name__ == "__main__":
        asyncio.run(main())
