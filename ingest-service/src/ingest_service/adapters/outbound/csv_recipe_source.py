"""Вихідний адаптер — читання рецептів із CSV-файлу набору Food.com."""

import ast
import asyncio
import csv
from itertools import islice
from typing import TextIO

from ingest_service.application.ports.outbound.recipe_source_port import RecipeSourcePort
from ingest_service.domain.raw_recipe import RawRecipe


class CsvRecipeSource(RecipeSourcePort):
    """Реалізує RecipeSourcePort для файлу RAW_recipes.csv.

    Особливості набору, які треба врахувати:
    - колонки tags, ingredients, steps, nutrition містять рядки виду "['a', 'b']",
      їх треба розібрати в списки (ast.literal_eval);
    - файл великий (~230 тис. рядків), тому читати його потоково, а не весь у пам'ять;
    - після кінця файлу почати спочатку, додаючи до id номер проходу (r-123-2),
      щоб повторні записи не перезаписували старі.
    """

    def __init__(self, csv_path: str) -> None:
        self._csv_path = csv_path
        self._file: TextIO | None = None
        self._reader: csv.DictReader | None = None
        self._lock = asyncio.Lock()
        self._pass_number = 0

    def _open_file(self) -> None:
        self._file = open(self._csv_path, newline="", encoding="utf-8")
        self._reader = csv.DictReader(self._file)
        self._pass_number += 1

    def _close_file(self) -> None:
        if self._file is not None:
            self._file.close()
        self._file = None
        self._reader = None

    def _read_batch(self, size: int) -> list[dict]:
        assert self._reader is not None
        return list(islice(self._reader, size))

    def _modify_id(self, raw_id: str) -> str:
        if self._pass_number == 1:
            return raw_id
        return f"{raw_id}-{self._pass_number}"

    def _row_to_raw_recipe(self, row: dict[str, str]) -> RawRecipe:
        nutrition = ast.literal_eval(row["nutrition"]) if row["nutrition"] else []
        return RawRecipe(
            source_id=self._modify_id(row["id"]),
            title=row["name"],
            chef_id=row["contributor_id"],
            cook_time_min=int(row["minutes"]),
            calories=float(nutrition[0]) if nutrition else None,
            tags=ast.literal_eval(row["tags"]) if row["tags"] else [],
            ingredients=ast.literal_eval(row["ingredients"]) if row["ingredients"] else [],
            steps=ast.literal_eval(row["steps"]) if row["steps"] else [],
            description=row["description"],
        )

    async def next_batch(self, size: int) -> list[RawRecipe]:
        async with self._lock:
            if self._reader is None:
                await asyncio.to_thread(self._open_file)
            batch = await asyncio.to_thread(self._read_batch, size)
            if len(batch) < size:
                await asyncio.to_thread(self._close_file)
            return [self._row_to_raw_recipe(row) for row in batch]
