"""Точка входу ingest-service.

Запуск (з кореня репозиторію):
    uv run --package ingest-service python -m ingest_service.main
"""

import asyncio
import logging.config

import yaml

from ingest_service.container import build_container
from ingest_service.settings import Settings


def setup_logging(path: str) -> None:
    """Налаштувати логування з YAML-файлу (див. config/logging.yaml)."""
    with open(path, encoding="utf-8") as f:
        logging.config.dictConfig(yaml.safe_load(f))


async def main() -> None:
    settings = Settings()
    setup_logging(settings.log_config)
    container = build_container(settings)

    await container.publisher.connect()
    try:
        await container.scheduler.run_forever()
    finally:
        await container.publisher.close()


if __name__ == "__main__":
    asyncio.run(main())
