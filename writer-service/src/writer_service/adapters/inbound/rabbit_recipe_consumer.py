"""Вхідний адаптер — споживач черги RabbitMQ.

Роль така сама, як у REST-контролера: отримати зовнішнє повідомлення,
перетворити його на виклик вхідного порту. Бізнес-логіки тут немає.
"""

import asyncio
import json
import logging

import aio_pika
from aio_pika.abc import AbstractIncomingMessage

from writer_service.application.ports.inbound.save_recipes_use_case import SaveRecipesUseCase

logger = logging.getLogger(__name__)


class RabbitRecipeConsumer:
    """Накопичує повідомлення в пачку і передає її в SaveRecipesUseCase.

    Ключові моменти:
    - обмінник exchange_name має тип fanout; екземпляр оголошує власну чергу
      queue_name (recipes.mongo, recipes.es або recipes.neo4j) і прив'язує її до обмінника,
      тому кожне повідомлення потрапляє в усі три черги;
    - channel.set_qos(prefetch_count=...) — обмежує кількість непідтверджених
      повідомлень (зворотний тиск);
    - пачка відправляється, коли набралося batch_size або минув batch_timeout_ms;
    - ack усіх повідомлень пачки — ЛИШЕ після успішного save_batch;
    - при помилці — nack(requeue=True), повідомлення повернуться в чергу.
    """

    def __init__(
        self,
        use_case: SaveRecipesUseCase,
        rabbit_url: str,
        exchange_name: str,
        queue_name: str,
        batch_size: int,
        batch_timeout_ms: int,
        prefetch_count: int,
    ) -> None:
        self._use_case = use_case
        self._rabbit_url = rabbit_url
        self._exchange_name = exchange_name
        self._queue_name = queue_name
        self._batch_size = batch_size
        self._batch_timeout_ms = batch_timeout_ms
        self._prefetch_count = prefetch_count
        self._connection = None
        self._channel = None
        self._current_batch = []
        self._current_messages = []
        self._timer_task = None

    async def start(self) -> None:
        """Підключитися, оголосити обмінник і чергу, прив'язати чергу, почати споживання."""
        self._connection = await aio_pika.connect_robust(self._rabbit_url)
        self._channel = await self._connection.channel()

        await self._channel.set_qos(prefetch_count=self._prefetch_count)
        exchange = await self._channel.declare_exchange(
            name=self._exchange_name, type=aio_pika.ExchangeType.FANOUT
        )
        queue = await self._channel.declare_queue(self._queue_name, durable=True)
        await queue.bind(exchange)
        await queue.consume(self._on_message)
        logger.info(f"RabbitMQ consumer started on queue: {self._queue_name}")

    async def _on_message(self, message: AbstractIncomingMessage) -> None:
        """Обробляє одне повідомлення, додає в пачку. Якщо пачка повна — зберігає."""
        data = json.loads(message.body.decode("utf-8"))

        self._current_batch.append(data)
        self._current_messages.append(message)
        if len(self._current_batch) == 1:
            self._start_timer()

        if len(self._current_batch) >= self._batch_size:
            await self._process_batch()

    def _start_timer(self) -> None:
        """Запускає фонове очікування, щоб відправити неповну пачку по тайм-ауту."""
        if self._timer_task and not self._timer_task.done():
            self._timer_task.cancel()

        async def timer() -> None:
            await asyncio.sleep(self._batch_timeout_ms / 1000.0)
            if self._current_batch:
                await self._process_batch()

        self._timer_task = asyncio.create_task(timer())

    async def _process_batch(self) -> None:
        """Відправляє пачку в use case і робить ack/nack."""
        if not self._current_batch:
            return

        if self._timer_task and not self._timer_task.done():
            self._timer_task.cancel()

        batch_to_process = self._current_batch[:]
        messages_to_process = self._current_messages[:]
        self._current_batch.clear()
        self._current_messages.clear()

        try:
            await self._use_case.save_batch(batch_to_process)
            for msg in messages_to_process:
                await msg.ack()
        except Exception as e:
            logger.error("Помилка обробки пачки: %s", e)
            for msg in messages_to_process:
                await msg.nack(requeue=True)

    async def stop(self) -> None:
        """Дописати поточну пачку і закрити з'єднання."""
        if self._timer_task and not self._timer_task.done():
            self._timer_task.cancel()
        if self._current_batch:
            await self._process_batch()
        if self._channel and not self._channel.is_closed:
            await self._channel.close()
        if self._connection and not self._connection.is_closed:
            await self._connection.close()
        logger.info(f"RabbitMQ consumer stopped on queue: {self._queue_name}")
