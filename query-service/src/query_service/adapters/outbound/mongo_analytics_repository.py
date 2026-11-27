"""Вихідний адаптер MongoDB для аналітики (завдання 14: map-reduce по шардах).

Чому aggregation pipeline, а не команда mapReduce: mapReduce у MongoDB застаріла
з версії 5.0, офіційна заміна — aggregation pipeline. Ідея та сама:

    map + combine  — кожен шард виконує $match і $group над СВОЇМИ документами
                     і повертає часткові підсумки (сума, кількість) по кожній кухні;
    shuffle/reduce — mongos отримує часткові підсумки від усіх шардів і досклеює їх
                     ще одним $group (сумує кількості, перераховує середні).

Шарди рахують паралельно, а по мережі передаються лише ~30 рядків (по одному
на кухню), а не 230 тисяч документів. Як саме MongoDB розділила роботу,
видно в explain: поле splitPipeline (shardsPart / mergerPart) і shards.
"""

import logging
import time
from typing import Any

from pymongo import AsyncMongoClient

from query_service.application.ports.outbound.analytics_ports import RecipeAnalyticsRepository
from query_service.domain.analytics import AggregationReport, CuisineStat, ShardWork

logger = logging.getLogger(__name__)

NO_CUISINE = "без кухні"


def build_pipeline(max_cook_time_min: int | None) -> list[dict]:
    pipeline: list[dict] = []
    if max_cook_time_min is not None:
        pipeline.append({"$match": {"cook_time_min": {"$lte": max_cook_time_min}}})
    pipeline += [
        {
            "$group": {
                "_id": {"$ifNull": ["$cuisine", NO_CUISINE]},
                "recipes": {"$sum": 1},
                # $avg пропускає null, тому рецепти без калорій середнє не псують
                "avg_calories": {"$avg": "$calories"},
                "avg_cook_time_min": {"$avg": "$cook_time_min"},
                "max_calories": {"$max": "$calories"},
            }
        },
        {"$sort": {"recipes": -1, "_id": 1}},
    ]
    return pipeline


def _find_key(obj: Any, key: str) -> Any:
    """Знайти перше входження ключа в глибоко вкладеному explain (формат залежить
    від версії MongoDB і від того, чи виконувався запит рушієм SBE)."""
    if isinstance(obj, dict):
        if key in obj:
            return obj[key]
        for value in obj.values():
            found = _find_key(value, key)
            if found is not None:
                return found
    elif isinstance(obj, list):
        for value in obj:
            found = _find_key(value, key)
            if found is not None:
                return found
    return None


def _stage_names(stages: list[dict] | None) -> list[str]:
    return [next(iter(stage)) for stage in stages or [] if stage]


def parse_explain(explain: dict) -> tuple[bool, str | None, list[ShardWork], list[str], list[str]]:
    """explain -> (чи розділено конвеєр, mergeType, робота шардів, стадії map, стадії reduce)."""
    split = explain.get("splitPipeline")
    shards_raw = explain.get("shards")
    shards: list[ShardWork] = []
    if isinstance(shards_raw, dict) and shards_raw:
        for name, shard_explain in shards_raw.items():
            stats = _find_key(shard_explain, "executionStats") or {}
            shards.append(
                ShardWork(
                    shard=name,
                    docs_examined=stats.get("totalDocsExamined"),
                    time_ms=stats.get("executionTimeMillis"),
                )
            )
    else:
        # Не шардований сервер: уся робота на одному вузлі.
        stats = _find_key(explain, "executionStats") or {}
        shards.append(
            ShardWork(
                shard="один сервер (без шардів)",
                docs_examined=stats.get("totalDocsExamined"),
                time_ms=stats.get("executionTimeMillis"),
            )
        )
    if split:
        return (
            True,
            explain.get("mergeType"),
            shards,
            _stage_names(split.get("shardsPart")),
            _stage_names(split.get("mergerPart")),
        )
    return False, explain.get("mergeType"), shards, [], []


def _round(value: float | None, digits: int = 1) -> float | None:
    return round(value, digits) if value is not None else None


class MongoRecipeAnalyticsRepository(RecipeAnalyticsRepository):
    def __init__(self, client: AsyncMongoClient, db_name: str) -> None:
        self._db = client[db_name]
        self._collection = self._db["recipes"]

    async def cuisine_stats(self, max_cook_time_min: int | None) -> AggregationReport:
        pipeline = build_pipeline(max_cook_time_min)

        started = time.perf_counter()
        cursor = await self._collection.aggregate(pipeline)
        rows = await cursor.to_list()
        total_ms = (time.perf_counter() - started) * 1000

        stats = [
            CuisineStat(
                cuisine=row["_id"],
                recipes=row["recipes"],
                avg_calories=_round(row.get("avg_calories")),
                avg_cook_time_min=_round(row.get("avg_cook_time_min")),
                max_calories=_round(row.get("max_calories")),
            )
            for row in rows
        ]

        try:
            explain = await self._db.command(
                {
                    "explain": {"aggregate": "recipes", "pipeline": pipeline, "cursor": {}},
                    "verbosity": "executionStats",
                }
            )
            split, merge_type, shards, shards_part, merger_part = parse_explain(explain)
        except Exception as exc:  # noqa: BLE001 — без плану сторінка все одно покаже результат
            logger.warning("Не вдалося отримати explain агрегації: %s", exc)
            split, merge_type, shards, shards_part, merger_part = False, None, [], [], []

        logger.info(
            "Агрегація за кухнями: %d груп, %.1f мс, шардів: %d", len(stats), total_ms, len(shards)
        )
        return AggregationReport(
            stats=stats,
            total_ms=round(total_ms, 1),
            split_pipeline=split,
            merge_type=merge_type,
            shards=shards,
            shards_part=shards_part,
            merger_part=merger_part,
        )
