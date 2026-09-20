"""Налаштування query-service (читаються з .env, див. .env.example)."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Папка сервісу (…/query-service), щоб шлях до конфігу логів не залежав від того,
# з якої папки запущено сервіс.
SERVICE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    mongo_url: str = "mongodb://localhost:27017"
    mongo_db: str = "recipes"

    es_url: str = "http://localhost:9200"
    es_index: str = "recipes"

    neo4j_url: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "change-me"

    redis_url: str = "redis://localhost:6379/0"

    rabbit_management_url: str = "http://localhost:15672"
    rabbit_queue: str = "recipes.ingest"

    search_cache_ttl_sec: int = 300
    ingest_default_rate: int = 10

    log_config: Path = SERVICE_DIR / "config" / "logging.yaml"
