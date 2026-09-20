"""Вхідний адаптер — споживач черги RabbitMQ.

Роль така сама, як у REST-контролера: отримати зовнішнє повідомлення,
перетворити його на виклик вхідного порту. Бізнес-логіки тут немає.
"""

from writer_service.application.ports.inbound.save_recipes_use_case import SaveRecipesUseCase


class RabbitRecipeConsumer:
    """Накопичує повідомлення в пачку і передає її в SaveRecipesUseCase.

    Ключові моменти:
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
        queue_name: str,
        batch_size: int,
        batch_timeout_ms: int,
        prefetch_count: int,
    ) -> None:
        self._use_case = use_case
        self._rabbit_url = rabbit_url
        self._queue_name = queue_name
        self._batch_size = batch_size
        self._batch_timeout_ms = batch_timeout_ms
        self._prefetch_count = prefetch_count

    async def start(self) -> None:
        """Підключитися, оголосити чергу, почати споживання."""
        raise NotImplementedError

    async def stop(self) -> None:
        """Дописати поточну пачку і закрити з'єднання."""
        raise NotImplementedError
