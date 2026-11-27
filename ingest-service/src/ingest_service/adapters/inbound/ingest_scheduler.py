"""Вхідний адаптер — планувальник, який «штовхає» застосунок.

У веб-сервісах вхідним адаптером зазвичай є REST-контролер: він отримує HTTP-запит
і викликає вхідний порт. Тут зовнішнього запиту немає, тому роль «того, хто запускає
логіку», виконує нескінченний asyncio-цикл, який кожні 100 мс викликає run_tick().
"""

import asyncio
import logging
import time

from ingest_service.application.ports.inbound.ingest_use_case import IngestUseCase

logger = logging.getLogger(__name__)


class IngestScheduler:
    def __init__(self, use_case: IngestUseCase, tick_seconds: float = 0.1) -> None:
        self._use_case = use_case
        self._tick_seconds = tick_seconds
        self._stopped = False

    async def run_forever(self) -> None:
        """Цикл: run_tick() -> asyncio.sleep(залишок такту).

        Враховується час виконання run_tick: якщо такт зайняв 0.03 с,
        спимо лише 0.07 с, щоб фактична швидкість відповідала заданій.
        Помилки одного такту логуються (ERROR), і робота продовжується:
        наприклад, короткий перезапуск RabbitMQ не має вбивати сервіс.
        """
        logger.info("Планувальник запущено, такт %.2f с", self._tick_seconds)
        published_total = 0
        last_report = time.monotonic()
        while not self._stopped:
            started = time.monotonic()
            try:
                published_total += await self._use_case.run_tick()
            except Exception:
                logger.exception("Помилка в такті, продовжуємо роботу")
                await asyncio.sleep(1)  # не засипати лог тисячами однакових помилок
            now = time.monotonic()
            if now - last_report >= 10:
                logger.info("Опубліковано за 10 с: %d", published_total)
                published_total, last_report = 0, now
            await asyncio.sleep(max(0.0, self._tick_seconds - (now - started)))
        logger.info("Планувальник зупинено")

    def stop(self) -> None:
        """Попросити цикл завершитися після поточного такту."""
        self._stopped = True
