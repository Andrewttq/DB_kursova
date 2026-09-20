"""Вихідні порти для рецептів — по одному інтерфейсу на кожне сховище.

Рецепт записується в три різні БД, і кожна отримує свій інтерфейс, бо в них
різні операції: у Mongo — документи, у Neo4j — вузли та зв'язки, в Elasticsearch —
індексація тексту. Прикладні сервіси залежать лише від цих інтерфейсів.
"""

from abc import ABC, abstractmethod

from writer_service.domain.recipe import Recipe


class RecipeDocumentRepository(ABC):
    """Картки рецептів у документній БД (реалізація: MongoRecipeRepository)."""

    @abstractmethod
    async def upsert_many(self, recipes: list[Recipe]) -> int:
        """Масовий запис (bulk). Повертає кількість записаних документів."""

    @abstractmethod
    async def delete(self, recipe_id: str) -> bool: ...


class RecipeGraphRepository(ABC):
    """Зв'язки рецепта в графовій БД (реалізація: Neo4jRecipeGraphRepository).

    Модель графа:
        (:Chef)-[:CREATED]->(:Recipe)-[:CONTAINS]->(:Ingredient)
        (:Recipe)-[:BELONGS_TO]->(:Cuisine)
    """

    @abstractmethod
    async def merge_many(self, recipes: list[Recipe]) -> int:
        """Створити/оновити вузли та зв'язки для пачки рецептів."""

    @abstractmethod
    async def delete(self, recipe_id: str) -> None: ...


class RecipeSearchIndexRepository(ABC):
    """Повнотекстовий індекс (реалізація: ElasticRecipeIndexRepository)."""

    @abstractmethod
    async def index_many(self, recipes: list[Recipe]) -> int:
        """Масова індексація (bulk API). Повертає кількість проіндексованих."""

    @abstractmethod
    async def delete(self, recipe_id: str) -> None: ...
