"""Вихідний адаптер — публікація рецептів у RabbitMQ через aio-pika."""

import asyncio
import logging

import aio_pika

from contracts import RecipeIngestedEvent, RecipePayload
from ingest_service.application.ports.outbound.recipe_publisher_port import RecipePublisherPort
from ingest_service.domain import cleaning
from ingest_service.domain.raw_recipe import RawRecipe

logger = logging.getLogger(__name__)


def to_event(raw: RawRecipe) -> RecipeIngestedEvent:
    """RawRecipe -> повідомлення контракту, з очищенням полів (domain/cleaning.py)."""
    return RecipeIngestedEvent(
        recipe=RecipePayload(
            id=cleaning.recipe_id(raw.source_id),
            title=raw.title.strip() or f"Recipe {raw.source_id}",
            chef_id=cleaning.chef_id(raw.chef_id),
            cuisine=cleaning.pick_cuisine(raw.tags),
            cook_time_min=cleaning.clean_cook_time(raw.cook_time_min),
            calories=cleaning.clean_calories(raw.calories),
            tags=raw.tags,
            ingredients=raw.ingredients,
            steps=raw.steps,
            description=raw.description or "",
        )
    )


class RabbitRecipePublisher(RecipePublisherPort):
    """Реалізує RecipePublisherPort.

    Кожен RawRecipe перетворюється на contracts.RecipeIngestedEvent
    і серіалізується в JSON (event.model_dump_json()).
    Публікація йде в обмінник типу fanout, а не в чергу: RabbitMQ сам копіює
    кожне повідомлення в усі прив'язані черги (recipes.mongo, recipes.es, recipes.neo4j).
    Обмінник durable; повідомлення persistent (не губляться при перезапуску RabbitMQ)
    або, для швидкості 5000/с, лише в пам'яті — див. Settings.rabbit_persistent.
    Черги теж оголошуються тут: якщо ingest запустили раніше за writer-service,
    повідомлення чекатимуть у черзі, а не зникнуть (fanout без черг їх викидає).
    Підтвердження публікації (publisher confirms) увімкнені; повідомлення пачки
    публікуються паралельно, тому чекаємо підтвердження всієї пачки разом, а не кожного окремо.
    """

    def __init__(
        self, rabbit_url: str, exchange_name: str, queue_names: list[str], persistent: bool = True
    ) -> None:
        self._rabbit_url = rabbit_url
        self._delivery_mode = (
            aio_pika.DeliveryMode.PERSISTENT if persistent else aio_pika.DeliveryMode.NOT_PERSISTENT
        )
        self._exchange_name = exchange_name
        self._queue_names = queue_names
        self._connection: aio_pika.abc.AbstractRobustConnection | None = None
        self._exchange: aio_pika.abc.AbstractExchange | None = None

    async def connect(self) -> None:
        """Відкрити з'єднання та канал, оголосити обмінник і черги (при старті)."""
        self._connection = await aio_pika.connect_robust(self._rabbit_url)
        channel = await self._connection.channel()
        self._exchange = await channel.declare_exchange(
            self._exchange_name, aio_pika.ExchangeType.FANOUT, durable=True
        )
        for name in self._queue_names:
            queue = await channel.declare_queue(name, durable=True)
            await queue.bind(self._exchange)
        logger.info("Підключено до RabbitMQ, обмінник %s", self._exchange_name)

    async def publish_batch(self, recipes: list[RawRecipe]) -> int:
        if self._exchange is None:
            raise RuntimeError("Спочатку викличте connect()")
        messages = [
            aio_pika.Message(
                body=to_event(r).model_dump_json().encode("utf-8"),
                content_type="application/json",
                delivery_mode=self._delivery_mode,
            )
            for r in recipes
        ]
        results = await asyncio.gather(
            *(self._exchange.publish(m, routing_key="") for m in messages),
            return_exceptions=True,
        )
        errors = [r for r in results if isinstance(r, Exception)]
        if errors:
            logger.error("Не опубліковано %d з %d: %s", len(errors), len(messages), errors[0])
        return len(messages) - len(errors)

    async def close(self) -> None:
        """Закрити з'єднання (викликається при зупинці сервісу)."""
        if self._connection is not None:
            await self._connection.close()
