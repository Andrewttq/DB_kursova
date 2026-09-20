"""Налаштування writer-service (читаються з .env, див. .env.example)."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Папка сервісу (…/writer-service), щоб шлях до конфігу логів не залежав від того,
# з якої папки запущено сервіс.
SERVICE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    rabbit_url: str = "amqp://guest:guest@localhost:5672/"
    rabbit_queue: str = "recipes.ingest"

    mongo_url: str = "mongodb://localhost:27017"
    mongo_db: str = "recipes"

    es_url: str = "http://localhost:9200"
    es_index: str = "recipes"

    neo4j_url: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "change-me"

    redis_url: str = "redis://localhost:6379/0"

    # Пачка закривається, коли набралося batch_size повідомлень
    # або минуло batch_timeout_ms від першого повідомлення в ній.
    writer_batch_size: int = 500
    writer_batch_timeout_ms: int = 200
    # Скільки непідтверджених повідомлень RabbitMQ може видати сервісу одночасно.
    # Це і є механізм зворотного тиску (backpressure).
    writer_prefetch_count: int = 1000

    log_config: Path = SERVICE_DIR / "config" / "logging.yaml"
