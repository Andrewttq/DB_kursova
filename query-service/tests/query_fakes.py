"""Фейкові адаптери для тестів без баз даних.

Фейк наслідує той самий порт, що й справжній адаптер, тому фасад не помічає різниці.
Саме це і дає гексагональна архітектура: логіку можна перевірити без Docker.
"""

from query_service.application.ports.outbound.chef_repositories import ChefReadRepository
from query_service.application.ports.outbound.recipe_repositories import (
    RecipeGraphReadRepository,
    RecipeReadRepository,
)
from query_service.application.ports.outbound.search_ports import (
    RecipeSearchRepository,
    SearchCachePort,
    SearchLogRepository,
)
from query_service.domain.chef import Chef
from query_service.domain.recipe import Recipe, Recommendation
from query_service.domain.search import SearchHit, SearchLogEntry


class FakeRecipes(RecipeReadRepository):
    def __init__(self, recipes: list[Recipe]) -> None:
        self.by_id = {r.id: r for r in recipes}

    async def find_by_id(self, recipe_id):
        return self.by_id.get(recipe_id)

    async def find_by_ids(self, recipe_ids):
        return [self.by_id[i] for i in recipe_ids if i in self.by_id]

    async def find_by_chef(self, chef_id, limit):
        return [r for r in self.by_id.values() if r.chef_id == chef_id][:limit]

    async def find_by_filter(self, cuisine, max_cook_time_min, max_calories, skip, limit):
        items = [r for r in self.by_id.values() if not cuisine or r.cuisine == cuisine]
        return items[skip : skip + limit]


class FakeChefs(ChefReadRepository):
    async def find_by_id(self, chef_id):
        return Chef(id=chef_id, full_name="Olena Kovalenko") if chef_id != "nobody" else None


class FakeGraph(RecipeGraphReadRepository):
    def __init__(self, similar=None, chef_recipes=None, broken=False) -> None:
        self.similar = similar or []
        self.chef_recipes = chef_recipes or []
        self.broken = broken

    async def find_similar_by_ingredients(self, recipe_id, limit):
        if self.broken:
            raise ConnectionError("neo4j down")
        return self.similar[:limit]

    async def find_recipe_ids_by_chef(self, chef_id, limit):
        if self.broken:
            raise ConnectionError("neo4j down")
        return self.chef_recipes[:limit]


class FakeSearch(RecipeSearchRepository):
    def __init__(self, hits: list[SearchHit]) -> None:
        self.hits = hits
        self.calls = 0

    async def search(self, text, cuisine, max_cook_time_min, max_calories, page, size):
        self.calls += 1
        return [h for h in self.hits if any(w in h.title.lower() for w in text.lower().split())]


class FakeCache(SearchCachePort):
    def __init__(self) -> None:
        self.store: dict[str, list[SearchHit]] = {}

    async def get(self, key):
        return self.store.get(key)

    async def put(self, key, hits, ttl_sec):
        self.store[key] = list(hits)


class FakeLog(SearchLogRepository):
    def __init__(self) -> None:
        self.entries: list[SearchLogEntry] = []

    async def append(self, entry):
        self.entries.insert(0, entry)

    async def recent(self, limit):
        return self.entries[:limit]


RECOMMENDATION = Recommendation(recipe_id="r2", title="Pasta", common_ingredients=3, score=0.4)
