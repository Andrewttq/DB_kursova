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
