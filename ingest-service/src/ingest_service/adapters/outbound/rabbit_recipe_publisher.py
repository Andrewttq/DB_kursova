"""Вихідний адаптер — публікація рецептів у RabbitMQ через aio-pika."""

from ingest_service.application.ports.outbound.recipe_publisher_port import RecipePublisherPort
from ingest_service.domain.raw_recipe import RawRecipe


class RabbitRecipePublisher(RecipePublisherPort):
    """Реалізує RecipePublisherPort.

    Кожен RawRecipe перетворюється на contracts.RecipeIngestedEvent
    і серіалізується в JSON (event.model_dump_json()).
    Публікація йде в обмінник типу fanout, а не в чергу: RabbitMQ сам копіює
    кожне повідомлення в усі прив'язані черги (recipes.mongo, recipes.es, recipes.neo4j).
    Обмінник має бути durable, а повідомлення — persistent, щоб вони
    не губилися при перезапуску RabbitMQ.
    """

    def __init__(self, rabbit_url: str, exchange_name: str) -> None:
        self._rabbit_url = rabbit_url
        self._exchange_name = exchange_name

    async def connect(self) -> None:
        """Відкрити з'єднання та канал, оголосити обмінник (викликається при старті)."""
        raise NotImplementedError

    async def publish_batch(self, recipes: list[RawRecipe]) -> int:
        raise NotImplementedError

    async def close(self) -> None:
        """Закрити з'єднання (викликається при зупинці сервісу)."""
        raise NotImplementedError
