"""Збирання залежностей (Dependency Injection вручну).

Це єдине місце, де «знають» про конкретні адаптери. Тут створюються реалізації
вихідних портів і передаються в прикладний сервіс через конструктор.
Щоб, наприклад, замінити CSV на генератор, досить змінити один рядок тут.
У тестах замість цього файлу можна зібрати сервіс із фейковими адаптерами.
"""

from dataclasses import dataclass

from ingest_service.adapters.inbound.ingest_scheduler import IngestScheduler
from ingest_service.adapters.outbound.csv_recipe_source import CsvRecipeSource
from ingest_service.adapters.outbound.rabbit_recipe_publisher import RabbitRecipePublisher
from ingest_service.adapters.outbound.redis_ingest_config_repository import (
    RedisIngestConfigRepository,
)
from ingest_service.adapters.outbound.redis_ingest_stats_repository import (
    RedisIngestStatsRepository,
)
from ingest_service.application.services.ingest_service import IngestService
from ingest_service.application.services.rate_limiter import RateLimiter
from ingest_service.settings import Settings


@dataclass
class Container:
    publisher: RabbitRecipePublisher
    scheduler: IngestScheduler


def build_container(settings: Settings) -> Container:
    # 1. Вихідні адаптери (конкретні реалізації портів)
    source = CsvRecipeSource(settings.ingest_csv_path)
    publisher = RabbitRecipePublisher(settings.rabbit_url, settings.rabbit_queue)
    config = RedisIngestConfigRepository(settings.redis_url, settings.ingest_default_rate)
    stats = RedisIngestStatsRepository(settings.redis_url)

    # 2. Прикладний шар отримує адаптери як інтерфейси
    service = IngestService(
        source=source,
        publisher=publisher,
        config=config,
        stats=stats,
        rate_limiter=RateLimiter(),
    )

    # 3. Вхідний адаптер отримує вхідний порт
    scheduler = IngestScheduler(service)
    return Container(publisher=publisher, scheduler=scheduler)
