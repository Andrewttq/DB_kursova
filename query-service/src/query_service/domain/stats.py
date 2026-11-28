"""Доменні класи статистики."""

from dataclasses import dataclass, field


@dataclass
class SystemStats:
    """Знімок стану системи для панелі моніторингу."""

    read_total: int  # прочитано ingest-service
    published_total: int  # опубліковано в брокер
    saved_total: dict[str, int]  # збережено за сховищами: mongo, es, neo4j
    failed_total: int
    write_rps: float  # збережено в MongoDB за останню секунду (з лічильників Redis)
    queue_depths: dict[str, int]  # повідомлень у чергах recipes.mongo / .es / .neo4j
    # середня швидкість за останні ~5 с, записів/с (різниця лічильників Redis за час)
    published_rps: float = 0.0
    saved_rps: dict[str, float] = field(default_factory=dict)


@dataclass
class IngestConfig:
    """Налаштування завантаження, які змінюються з UI."""

    rate_per_sec: int
    running: bool
