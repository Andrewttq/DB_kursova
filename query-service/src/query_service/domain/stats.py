"""Доменні класи статистики."""

from dataclasses import dataclass


@dataclass
class SystemStats:
    """Знімок стану системи для панелі моніторингу."""

    read_total: int  # прочитано ingest-service
    published_total: int  # опубліковано в брокер
    saved_total: int  # збережено writer-service
    failed_total: int
    write_rps: float  # збережено за останню секунду (з лічильників Redis)
    queue_depth: int  # повідомлень у черзі RabbitMQ


@dataclass
class IngestConfig:
    """Налаштування завантаження, які змінюються з UI."""

    rate_per_sec: int
    running: bool
