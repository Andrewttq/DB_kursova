"""Споживач RabbitMQ: неповна пачка, яку закриває таймер, теж зберігається і отримує ack."""

import asyncio

from contracts import RecipeIngestedEvent, RecipePayload
from writer_service.adapters.inbound.rabbit_recipe_consumer import RabbitRecipeConsumer


class FakeUseCase:
    def __init__(self) -> None:
        self.saved = 0

    async def save_batch(self, batch: list[RecipeIngestedEvent]) -> None:
        await asyncio.sleep(0.01)  # запис у сховище займає час
        self.saved += len(batch)


class FakeMessage:
    def __init__(self, body: bytes) -> None:
        self.body = body
        self.acked = False

    async def ack(self) -> None:
        self.acked = True

    async def nack(self, requeue: bool = True) -> None:
        pass

    async def reject(self, requeue: bool = False) -> None:
        pass


BODY = (
    RecipeIngestedEvent(
        recipe=RecipePayload(
            id="r1",
            title="Soup",
            chef_id="c1",
            cuisine="italian",
            cook_time_min=10,
            calories=100,
            tags=[],
            ingredients=["salt"],
            steps=["boil"],
            description="",
        )
    )
    .model_dump_json()
    .encode()
)


async def test_partial_batch_closed_by_timer_is_saved_and_acked() -> None:
    use_case = FakeUseCase()
    consumer = RabbitRecipeConsumer(use_case, "", "recipes", "q", 500, 50, 1000)
    messages = [FakeMessage(BODY) for _ in range(1234)]  # дві повні пачки + 234 по таймеру

    for message in messages:
        await consumer._on_message(message)
    await asyncio.sleep(0.3)

    assert use_case.saved == 1234
    assert all(m.acked for m in messages)


async def test_messages_arriving_during_timer_flush_are_not_lost() -> None:
    """Нове повідомлення під час запису пачки таймером не скасовує цей запис."""

    class SlowUseCase(FakeUseCase):
        async def save_batch(self, batch: list[RecipeIngestedEvent]) -> None:
            await asyncio.sleep(0.03)
            self.saved += len(batch)

    use_case = SlowUseCase()
    consumer = RabbitRecipeConsumer(use_case, "", "recipes", "q", 500, 10, 1000)
    messages = [FakeMessage(BODY) for _ in range(200)]

    for message in messages:  # повідомлення приходять повільно, пачки закриває таймер
        await consumer._on_message(message)
        await asyncio.sleep(0.002)
    await asyncio.sleep(0.3)

    assert use_case.saved == 200
    assert all(m.acked for m in messages)


async def test_batches_are_written_one_at_a_time() -> None:
    """Поки пишеться одна пачка, наступна лише набирається: записів паралельно немає."""

    class TrackingUseCase(FakeUseCase):
        def __init__(self) -> None:
            super().__init__()
            self.running = 0
            self.max_running = 0
            self.sizes: list[int] = []

        async def save_batch(self, batch: list[RecipeIngestedEvent]) -> None:
            self.running += 1
            self.max_running = max(self.max_running, self.running)
            await asyncio.sleep(0.02)
            self.sizes.append(len(batch))
            self.saved += len(batch)
            self.running -= 1

    use_case = TrackingUseCase()
    consumer = RabbitRecipeConsumer(use_case, "", "recipes", "q", 100, 10, 1000)
    messages = [FakeMessage(BODY) for _ in range(1000)]

    # як aio_pika: кожне повідомлення обробляється окремою задачею
    await asyncio.gather(*(consumer._on_message(m) for m in messages))
    await asyncio.sleep(0.5)

    assert use_case.max_running == 1
    assert use_case.saved == 1000
    assert all(m.acked for m in messages)
