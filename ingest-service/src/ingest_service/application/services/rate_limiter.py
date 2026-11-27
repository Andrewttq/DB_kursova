"""Обчислення розміру пачки за заданою швидкістю."""


class RateLimiter:
    """Перетворює швидкість (записів/с) на розмір пачки для одного такту.

    Приклад: швидкість 500 записів/с, такт триває 0,1 с -> пачка 50.
    Алгоритм — маркерне відро (token bucket): за кожен такт накопичується
    rate * tick_seconds маркерів, ціла частина йде в пачку, дробовий залишок
    переноситься на наступний такт (інакше швидкість 15/с давала б 10/с).
    """

    def __init__(self, tick_seconds: float = 0.1) -> None:
        self._tick_seconds = tick_seconds
        self._tokens = 0.0

    def batch_size(self, rate_per_sec: int) -> int:
        """Скільки записів прочитати за один такт при заданій швидкості."""
        self._tokens += max(rate_per_sec, 0) * self._tick_seconds
        size = int(self._tokens)
        self._tokens -= size
        return size

    def reset(self) -> None:
        """Скинути залишок (після паузи, щоб не було «залпу» накопичених маркерів)."""
        self._tokens = 0.0
