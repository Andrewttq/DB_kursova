"""Вхідний адаптер — планувальник, який «штовхає» застосунок.

У веб-сервісах вхідним адаптером зазвичай є REST-контролер: він отримує HTTP-запит
і викликає вхідний порт. Тут зовнішнього запиту немає, тому роль «того, хто запускає
логіку», виконує нескінченний asyncio-цикл, який раз на секунду викликає run_tick().
"""

from ingest_service.application.ports.inbound.ingest_use_case import IngestUseCase


class IngestScheduler:
    def __init__(self, use_case: IngestUseCase, tick_seconds: float = 1.0) -> None:
        self._use_case = use_case
        self._tick_seconds = tick_seconds
        self._stopped = False

    async def run_forever(self) -> None:
        """Цикл: run_tick() -> asyncio.sleep(залишок такту).

        Враховувати час виконання run_tick: якщо такт зайняв 0.3 с,
        спати лише 0.7 с, щоб фактична швидкість відповідала заданій.
        Помилки одного такту логувати (ERROR) і продовжувати роботу.
        """
        raise NotImplementedError

    def stop(self) -> None:
        """Попросити цикл завершитися після поточного такту."""
        self._stopped = True
