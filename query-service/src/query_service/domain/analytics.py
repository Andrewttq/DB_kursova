"""Доменні класи аналітики (завдання 14: один запит, зібраний з усіх шардів)."""

from dataclasses import dataclass, field


@dataclass
class CuisineStat:
    """Результат агрегації для однієї кухні."""

    cuisine: str
    recipes: int
    avg_calories: float | None
    avg_cook_time_min: float | None
    max_calories: float | None


@dataclass
class ShardWork:
    """Що зробив один шард на етапі map (дані з explain)."""

    shard: str
    docs_examined: int | None
    time_ms: int | None


@dataclass
class AggregationReport:
    """Результат агрегації разом з тим, як MongoDB її виконала.

    shards_part — стадії, які кожен шард виконав над своєю частиною даних (map + combine);
    merger_part — стадії, якими mongos склеїв часткові результати (reduce).
    Якщо кластер не шардований, shards містить один елемент, а split_pipeline=False.
    """

    stats: list[CuisineStat]
    total_ms: float
    split_pipeline: bool
    merge_type: str | None
    shards: list[ShardWork] = field(default_factory=list)
    shards_part: list[str] = field(default_factory=list)
    merger_part: list[str] = field(default_factory=list)
