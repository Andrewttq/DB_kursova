"""Демонстрація запису і читання лічильника ingest-service у Redis."""

import asyncio
import logging

from redis.asyncio import Redis

from ingest_service.adapters.outbound.csv_recipe_source import CsvRecipeSource
from ingest_service.adapters.outbound.redis_ingest_stats_repository import (
    RedisIngestStatsRepository,
)
from ingest_service.main import setup_logging
from ingest_service.settings import Settings


async def main() -> None:
    settings = Settings()
    setup_logging(settings.log_config)
    source = CsvRecipeSource(settings.demo_csv_path)

    batch = await source.read_batch(100)
    logging.log.info("Прочитано рецептів: %s, перший: %s", len(batch), batch[0].title)

    stats = RedisIngestStatsRepository(settings.redis_url)
    await stats.incr_read(len(batch))

    redis = Redis.from_url(settings.redis_url)
    value = await redis.get("stats:read")

    text = value.decode("utf-8") if isinstance(value, bytes) else str(value)
    logging.log.info("stats:read у Redis: %s", text)

    await redis.aclose()


if __name__ == "__main__":
    asyncio.run(main())
