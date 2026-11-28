from ingest_service.application.services.rate_limiter import RateLimiter


def total_per_second(rate: int) -> int:
    limiter = RateLimiter(tick_seconds=0.1)
    return sum(limiter.batch_size(rate) for _ in range(10))  # 10 тактів = 1 секунда


def test_exact_rate_per_second():
    for rate in (10, 15, 500, 5000, 1234):
        assert total_per_second(rate) == rate


def test_fraction_is_carried_to_next_tick():
    limiter = RateLimiter(tick_seconds=0.1)
    # 15/с -> 1.5 за такт: 1, 2, 1, 2 ...
    assert [limiter.batch_size(15) for _ in range(4)] == [1, 2, 1, 2]


def test_slow_tick_gives_bigger_batch():
    """Такт тривав 0,4 с замість 0,1 — пачка вчетверо більша, швидкість не падає."""
    now = [0.0]
    limiter = RateLimiter(tick_seconds=0.1, clock=lambda: now[0])
    assert limiter.batch_size(5000) == 500  # перший такт рахується як звичайний
    now[0] += 0.4
    assert limiter.batch_size(5000) == 2000
    now[0] += 30  # довга пауза: не більше секунди «наздоганяння»
    assert limiter.batch_size(5000) == 5000
