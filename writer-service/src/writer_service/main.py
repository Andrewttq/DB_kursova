"""Точка входу writer-service.

Запуск (з кореня репозиторію):
    uv run --package writer-service python -m writer_service.main
"""

import asyncio
import logging.config

import yaml

from writer_service.container import build_container
from writer_service.settings import Settings


def setup_logging(path: str) -> None:
    with open(path, encoding="utf-8") as f:
        logging.config.dictConfig(yaml.safe_load(f))


async def main() -> None:
    settings = Settings()
    setup_logging(settings.log_config)
    container = build_container(settings)

    await container.es_index.ensure_index()
    await container.consumer.start()
    try:
        await asyncio.Event().wait()  # працюємо, доки процес не зупинять (Ctrl+C)
    finally:
        await container.consumer.stop()
        await container.close()


if __name__ == "__main__":
    asyncio.run(main())
