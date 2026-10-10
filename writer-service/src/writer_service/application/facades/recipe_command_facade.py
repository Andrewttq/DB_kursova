"""Фасад — реалізація вхідного порту SaveRecipesUseCase.

Фасад не містить роботи з БД сам, він координує сервіси. Запущено три екземпляри
writer-service з однаковим кодом, кожен читає власну чергу і пише у власне сховище.
Які сервіси викликати, визначає роль екземпляра (налаштування WRITER_ROLE):
    mongo -> RecipeInformationService + ChefService (MongoDB)
    es    -> RecipeIndexService (Elasticsearch)
    neo4j -> RecipeRelationService (Neo4j)
WriteStatsService (Redis) спільний для всіх ролей і веде лічильник своєї ролі.
Завдяки поділу повільний запис у граф не затримує підтвердження для MongoDB
та Elasticsearch. Джерелом істини є MongoDB: індекс і граф можна перебудувати з неї.
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
        role: str,
        recipes: RecipeInformationService,
        chefs: ChefService,
        relations: RecipeRelationService,
        index: RecipeIndexService,
        stats: WriteStatsService,
    ) -> None:
        self._role = role
        self._recipes = recipes
        self._chefs = chefs
        self._relations = relations
        self._index = index
        self._stats = stats

    async def save_batch(self, events: list[RecipeIngestedEvent]) -> int:
        """1. mappers: події -> Recipe та Chef;
        2. залежно від ролі екземпляра:
           mongo — recipes.save_many + chefs.save_many,
           es    — index.index_many,
           neo4j — relations.register_many (уся пачка одним запитом UNWIND);
        3. stats.on_saved(...). При помилці — stats.on_failed(...) і прокинути виняток,
           щоб споживач НЕ підтвердив повідомлення і RabbitMQ доставив їх повторно.
        """
        raise NotImplementedError
