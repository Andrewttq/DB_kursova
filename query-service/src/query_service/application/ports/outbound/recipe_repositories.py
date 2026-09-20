"""Вихідні порти для читання рецептів."""

from abc import ABC, abstractmethod

from query_service.domain.recipe import Recipe, Recommendation


class RecipeReadRepository(ABC):
    """Картки рецептів (реалізація: MongoRecipeReadRepository)."""

    @abstractmethod
    async def find_by_id(self, recipe_id: str) -> Recipe | None: ...

    @abstractmethod
    async def find_by_ids(self, recipe_ids: list[str]) -> list[Recipe]: ...

    @abstractmethod
    async def find_by_filter(
        self,
        cuisine: str | None,
        max_cook_time_min: int | None,
        max_calories: float | None,
        skip: int,
        limit: int,
    ) -> list[Recipe]: ...


class RecipeGraphReadRepository(ABC):
    """Зв'язки в графі (реалізація: Neo4jRecipeGraphReadRepository)."""

    @abstractmethod
    async def find_similar_by_ingredients(
        self, recipe_id: str, limit: int
    ) -> list[Recommendation]: ...

    @abstractmethod
    async def find_recipe_ids_by_chef(self, chef_id: str, limit: int) -> list[str]: ...
