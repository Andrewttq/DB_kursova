"""Такт ingest-service з фейковими портами (без CSV, RabbitMQ і Redis)."""

from ingest_service.application.ports.outbound.ingest_config_port import IngestConfigPort
from ingest_service.application.ports.outbound.ingest_stats_port import IngestStatsPort
from ingest_service.application.ports.outbound.recipe_publisher_port import RecipePublisherPort
from ingest_service.application.ports.outbound.recipe_source_port import RecipeSourcePort
from ingest_service.application.services.ingest_service import IngestService
from ingest_service.application.services.rate_limiter import RateLimiter
from ingest_service.domain.raw_recipe import RawRecipe


class Source(RecipeSourcePort):
    async def next_batch(self, size):
        return [RawRecipe(str(i), f"t{i}", "1", 10) for i in range(size)]


class Publisher(RecipePublisherPort):
    def __init__(self):
        self.sent = 0

    async def publish_batch(self, recipes):
        self.sent += len(recipes)
        return len(recipes)


class Config(IngestConfigPort):
    def __init__(self, rate, running=True):
        self.rate, self.running = rate, running

    async def get_rate(self):
        return self.rate

    async def is_running(self):
        return self.running


class Stats(IngestStatsPort):
    def __init__(self):
        self.read = self.published = 0

    async def incr_read(self, count):
        self.read += count

    async def incr_published(self, count):
        self.published += count


def make(rate, running=True):
    pub, stats = Publisher(), Stats()
    svc = IngestService(Source(), pub, Config(rate, running), stats, RateLimiter(0.1))
    return svc, pub, stats


async def test_one_second_of_ticks_publishes_rate_records():
    svc, pub, stats = make(500)
    for _ in range(10):
        await svc.run_tick()
    assert pub.sent == 500
    assert stats.read == stats.published == 500


async def test_stopped_generator_does_nothing():
    svc, pub, _ = make(500, running=False)
    assert await svc.run_tick() == 0
    assert pub.sent == 0
