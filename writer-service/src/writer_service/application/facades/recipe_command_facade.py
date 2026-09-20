"""Фасад — реалізація вхідного порту SaveRecipesUseCase.

Фасад не містить роботи з БД сам, він координує кілька сервісів в одну операцію:
    RabbitRecipeConsumer -> RecipeCommandFacade -> RecipeInformationService (Mongo)
                                                -> ChefService (Mongo)
                                                -> RecipeRelationService (Neo4j)
                                                -> RecipeIndexService (Elasticsearch)
                                                -> WriteStatsService (Redis)
Порядок важливий: спочатку MongoDB як джерело істини, потім Neo4j та Elasticsearch,
які за потреби можна перебудувати з Mongo.
"""

from contracts import RecipeIngestedEvent
from writer_service.application.ports.inbound.save_recipes_use_case import SaveRecipesUseCase
from writer_service.application.services.chef_service import ChefService
from writer_service.application.services.recipe_services import (
    RecipeIndexService,
    RecipeInformationService,
    RecipeRelationService,
)
from writer_service.application.services.write_stats_service import WriteStatsService


class RecipeCommandFacade(SaveRecipesUseCase):
    def __init__(
        self,
        recipes: RecipeInformationService,
        chefs: ChefService,
        relations: RecipeRelationService,
        index: RecipeIndexService,
        stats: WriteStatsService,
    ) -> None:
        self._recipes = recipes
        self._chefs = chefs
        self._relations = relations
        self._index = index
        self._stats = stats

    async def save_batch(self, events: list[RecipeIngestedEvent]) -> int:
        """1. mappers: події -> Recipe та Chef;
        2. recipes.save_many + chefs.save_many (Mongo);
        3. relations.register_many (Neo4j) і index.index_many (ES) — можна паралельно
           через asyncio.gather, бо вони не залежать одне від одного;
        4. stats.on_saved(...). При помилці — stats.on_failed(...) і прокинути виняток,
           щоб споживач НЕ підтвердив повідомлення і RabbitMQ доставив їх повторно.
        """
        raise NotImplementedError
