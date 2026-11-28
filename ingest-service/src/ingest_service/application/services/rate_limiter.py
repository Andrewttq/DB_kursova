"""Обчислення розміру пачки за заданою швидкістю."""

from collections.abc import Callable

# Після довгої паузи «наздоганяємо» не більше ніж за секунду, щоб не було залпу.
MAX_CATCH_UP_SEC = 1.0


class RateLimiter:
    """Перетворює швидкість (записів/с) на розмір пачки для одного такту.

    Приклад: швидкість 500 записів/с, такт триває 0,1 с -> пачка 50.
    Алгоритм — маркерне відро (token bucket): за кожен такт накопичується
    rate * тривалість такту маркерів, ціла частина йде в пачку, дробовий залишок
    переноситься на наступний такт (інакше швидкість 15/с давала б 10/с).

    Якщо передано clock (time.monotonic), тривалість такту береться за годинником:
    коли публікація пачки займає довше за tick_seconds (RabbitMQ чекає запису на диск),
    наступна пачка більша, і середня швидкість лишається заданою, а не падає.
    Без clock кожен такт вважається рівним tick_seconds (так зручно в тестах).
    """

    def __init__(self, tick_seconds: float = 0.1, clock: Callable[[], float] | None = None) -> None:
        self._tick_seconds = tick_seconds
        self._clock = clock
        self._last: float | None = None
        self._tokens = 0.0

    def _elapsed(self) -> float:
        if self._clock is None:
            return self._tick_seconds
        now = self._clock()
        elapsed = self._tick_seconds if self._last is None else now - self._last
        self._last = now
        return min(elapsed, MAX_CATCH_UP_SEC)

    def batch_size(self, rate_per_sec: int) -> int:
        """Скільки записів прочитати за цей такт при заданій швидкості."""
        self._tokens += max(rate_per_sec, 0) * self._elapsed()
        size = int(self._tokens)
        self._tokens -= size
        return size

    def reset(self) -> None:
        """Скинути залишок (після паузи, щоб не було «залпу» накопичених маркерів)."""
        self._tokens = 0.0
        self._last = None
