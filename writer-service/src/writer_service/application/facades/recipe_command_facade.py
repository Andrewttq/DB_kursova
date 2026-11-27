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

import logging
import time

from contracts import RecipeIngestedEvent
from writer_service.application import mappers
from writer_service.application.ports.inbound.save_recipes_use_case import SaveRecipesUseCase
from writer_service.application.services.chef_service import ChefService
from writer_service.application.services.recipe_services import (
    RecipeIndexService,
    RecipeInformationService,
    RecipeRelationService,
)
from writer_service.application.services.write_stats_service import WriteStatsService

logger = logging.getLogger(__name__)


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
        if not events:
            return 0
        recipes = [mappers.recipe_from_event(e) for e in events]
        started = time.perf_counter()
        try:
            if self._role == "mongo":
                saved = await self._recipes.save_many(recipes)
                await self._chefs.save_many([mappers.chef_from_event(e) for e in events])
            elif self._role == "es":
                saved = await self._index.index_many(recipes)
            elif self._role == "neo4j":
                saved = await self._relations.register_many(recipes)
            else:
                raise ValueError(f"Невідома роль writer-service: {self._role}")
        except Exception:
            await self._stats.on_failed(1)
            logger.exception("Пачку з %d рецептів не записано в %s", len(recipes), self._role)
            raise
        await self._stats.on_saved(saved)
        took_ms = (time.perf_counter() - started) * 1000
        logger.info("%s: записано %d з %d за %.0f мс", self._role, saved, len(recipes), took_ms)
        return saved
