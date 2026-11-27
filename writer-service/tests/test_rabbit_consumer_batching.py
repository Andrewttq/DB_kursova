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
