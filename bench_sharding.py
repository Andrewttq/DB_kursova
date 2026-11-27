"""Завдання 13: порівняння швидкості запису на один шард і на три шарди.

Що вимірюємо. Обидві колекції живуть в одному кластері (через mongos), різниця лише в тому,
як розкладено дані:
    bench.one_shard    — НЕ шардована колекція: уся лежить на первинному шарді бази,
                         ніби інших шардів немає;
    bench.three_shards — шардована за { _id: "hashed" }: документи рівномірно
                         розкидані по трьох шардах.
Пишемо однаково для обох: bulk_write(ReplaceOne(upsert=True), ordered=False) пачками
по --batch документів, як це робить writer-service, з --workers паралельними записувачами.
Кожен прогін повторюється --repeat разів, у таблицю йде медіана.

Запуск (кластер з docker-compose.sharded.yml має бути піднятий):
    uv run --package writer-service python scripts/bench_sharding.py
    uv run --package writer-service python scripts/bench_sharding.py --docs 50000 --workers 1 4 8
Додатково можна порівняти з окремим сервером MongoDB без шардингу (docker-compose.yml):
    ... --standalone-url mongodb://localhost:27017

Результат: таблиця в консолі та файл docs/bench_sharding.md (для звіту).
"""

import argparse
import asyncio
import csv
import random
import statistics
import string
import time
from datetime import datetime
from pathlib import Path

from pymongo import AsyncMongoClient, ReplaceOne

DB = "bench"
CSV_PATH = Path("data/RAW_recipes.csv")
REPORT_PATH = Path("docs/bench_sharding.md")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("--mongos-url", default="mongodb://localhost:27018")
    p.add_argument("--standalone-url", default=None, help="окремий mongod без шардів (необов.)")
    p.add_argument("--docs", type=int, default=20_000, help="скільки документів писати")
    p.add_argument("--batch", type=int, default=500, help="розмір пачки bulk_write")
    p.add_argument("--workers", type=int, nargs="+", default=[1, 4, 8])
    p.add_argument("--repeat", type=int, default=3)
    return p.parse_args()


def load_docs(n: int) -> list[dict]:
    """Справжні рецепти з CSV, якщо файл є; інакше схожі за розміром синтетичні документи."""
    docs: list[dict] = []
    if CSV_PATH.exists():
        with CSV_PATH.open(encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                docs.append(
                    {
                        "_id": f"r-{row['id']}",
                        "title": row["name"],
                        "chef_id": f"c-{row['contributor_id']}",
                        "cook_time_min": int(row["minutes"]) if row["minutes"].isdigit() else None,
                        "description": row["description"],
                        "steps": row["steps"],
                        "ingredients": row["ingredients"],
                    }
                )
                if len(docs) >= n:
                    break
    rng = random.Random(42)
    while len(docs) < n:
        i = len(docs)
        words = [
            "".join(rng.choices(string.ascii_lowercase, k=rng.randint(3, 9))) for _ in range(60)
        ]
        docs.append(
            {
                "_id": f"r-synthetic-{i}",
                "title": " ".join(words[:4]),
                "chef_id": f"c-{rng.randint(1, 30000)}",
                "cook_time_min": rng.randint(5, 240),
                "description": " ".join(words[4:30]),
                "steps": [" ".join(words[j : j + 8]) for j in range(30, 60, 8)],
                "ingredients": words[:9],
            }
        )
    return docs


def save_report(lines: list[str]) -> None:
    REPORT_PATH.parent.mkdir(exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


async def write_all(collection, docs: list[dict], batch: int, workers: int) -> float:
    """Записати всі документи; повертає документів за секунду."""
    batches = [docs[i : i + batch] for i in range(0, len(docs), batch)]
    queue: asyncio.Queue = asyncio.Queue()
    for b in batches:
        queue.put_nowait(b)

    async def worker() -> None:
        while not queue.empty():
            chunk = queue.get_nowait()
            ops = [ReplaceOne({"_id": d["_id"]}, d, upsert=True) for d in chunk]
            await collection.bulk_write(ops, ordered=False)

    started = time.perf_counter()
    await asyncio.gather(*(worker() for _ in range(workers)))
    return len(docs) / (time.perf_counter() - started)


async def prepare(client: AsyncMongoClient, name: str, sharded: bool) -> None:
    db = client[DB]
    await db.drop_collection(name)
    if sharded:
        await client.admin.command("enableSharding", DB)
        await client.admin.command("shardCollection", f"{DB}.{name}", key={"_id": "hashed"})
    else:
        await db.create_collection(name)


async def shard_distribution(client: AsyncMongoClient, name: str) -> dict[str, int]:
    """Скільки документів лежить на кожному шарді ($collStats через mongos)."""
    try:
        cursor = await client[DB][name].aggregate([{"$collStats": {"count": {}}}])
        rows = await cursor.to_list()
        return {row.get("shard", "standalone"): row["count"] for row in rows}
    except Exception as exc:  # noqa: BLE001
        return {"(невідомо)": 0, "error": str(exc)}  # type: ignore[dict-item]


async def run_target(
    client: AsyncMongoClient, name: str, sharded: bool, docs: list[dict], args
) -> tuple[dict[int, float], dict[str, int]]:
    results: dict[int, float] = {}
    for workers in args.workers:
        speeds = []
        for _ in range(args.repeat):
            await prepare(client, name, sharded)
            speeds.append(await write_all(client[DB][name], docs, args.batch, workers))
        results[workers] = statistics.median(speeds)
        print(f"  {name:<14} workers={workers:<3} {results[workers]:>9.0f} док/с")
    return results, await shard_distribution(client, name)


async def main() -> None:
    args = parse_args()
    docs = load_docs(args.docs)
    src = "CSV" if not docs[0]["_id"].startswith("r-synthetic") else "синтетичні"
    print(f"Документів: {len(docs)} ({src}), пачка {args.batch}, повторів {args.repeat}")

    targets: list[tuple[str, AsyncMongoClient, str, bool]] = []
    mongos = AsyncMongoClient(args.mongos_url)
    shards = await mongos.admin.command("listShards")
    shard_names = [s["_id"] for s in shards["shards"]]
    print(f"Шарди в кластері: {', '.join(shard_names)}")
    targets.append(("1 шард (колекція не шардована)", mongos, "one_shard", False))
    targets.append((f"{len(shard_names)} шарди (hashed _id)", mongos, "three_shards", True))
    standalone = None
    if args.standalone_url:
        standalone = AsyncMongoClient(args.standalone_url)
        targets.insert(0, ("окремий mongod без кластера", standalone, "standalone", False))

    table: list[tuple[str, dict[int, float], dict[str, int]]] = []
    for label, client, name, sharded in targets:
        print(f"\n{label}")
        results, dist = await run_target(client, name, sharded, docs, args)
        table.append((label, results, dist))

    # ---------- звіт ----------
    head = "| Конфігурація | " + " | ".join(f"{w} записувач(ів), док/с" for w in args.workers)
    lines = [
        f"# Швидкість запису: 1 шард проти {len(shard_names)} (завдання 13)",
        "",
        f"Дата: {datetime.now():%Y-%m-%d %H:%M}. Документів: {len(docs)} ({src}), "
        f"пачка bulk_write: {args.batch}, ordered=False, медіана з {args.repeat} прогонів.",
        "",
        head + " |",
        "|---|" + "---:|" * len(args.workers),
    ]
    for label, results, _ in table:
        lines.append(f"| {label} | " + " | ".join(f"{results[w]:.0f}" for w in args.workers) + " |")
    base = table[-2][1] if len(table) >= 2 else None
    sharded_res = table[-1][1]
    if base:
        lines += ["", "Прискорення 3 шарди / 1 шард:"]
        for w in args.workers:
            lines.append(f"- {w} записувач(ів): x{sharded_res[w] / base[w]:.2f}")
    lines += ["", "## Розподіл документів після запису", ""]
    for label, _, dist in table:
        lines.append(f"- {label}: " + ", ".join(f"{k}: {v}" for k, v in dist.items()))
    save_report(lines)
    print("\n" + "\n".join(lines))
    print(f"\nЗбережено: {REPORT_PATH}")

    for _, client, name, _ in targets:  # прибираємо за собою тестові дані
        await client[DB].drop_collection(name)
    await mongos.close()
    if standalone:
        await standalone.close()


if __name__ == "__main__":
    asyncio.run(main())
