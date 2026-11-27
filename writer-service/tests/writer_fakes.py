"""Фейкові сховища для тестів writer-service без баз даних."""

from writer_service.application.ports.outbound.chef_repositories import ChefRepository
from writer_service.application.ports.outbound.recipe_repositories import (
    RecipeDocumentRepository,
    RecipeGraphRepository,
    RecipeSearchIndexRepository,
)
from writer_service.application.ports.outbound.stats_repositories import WriteStatsRepository


class FakeStore(RecipeDocumentRepository, RecipeGraphRepository, RecipeSearchIndexRepository):
    """Одне сховище «словник id -> рецепт», що вдає з себе будь-яку з трьох БД."""

    def __init__(self, broken: bool = False) -> None:
        self.data = {}
        self.broken = broken

    async def _save(self, recipes):
        if self.broken:
            raise ConnectionError("db down")
        for r in recipes:
            self.data[r.id] = r  # upsert: повторний запис перезаписує, а не дублює
        return len(recipes)

    async def upsert_many(self, recipes):
        return await self._save(recipes)

    async def merge_many(self, recipes):
        return await self._save(recipes)

    async def index_many(self, recipes):
        return await self._save(recipes)

    async def delete(self, recipe_id):
        return self.data.pop(recipe_id, None) is not None


class FakeChefs(ChefRepository):
    def __init__(self) -> None:
        self.data = {}
        self.calls = []

    async def upsert_many(self, chefs):
        self.calls.append(len(chefs))
        for c in chefs:
            self.data[c.id] = c
        return len(chefs)


class FakeStats(WriteStatsRepository):
    def __init__(self) -> None:
        self.saved = 0
        self.failed = 0

    async def incr_saved(self, count):
        self.saved += count

    async def incr_failed(self, count):
        self.failed += count
