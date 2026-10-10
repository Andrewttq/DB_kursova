"""Налаштування сервісу, які читаються з файлу .env або змінних оточення.

pydantic-settings автоматично зіставляє назву поля зі змінною оточення без урахування
регістру: поле `rabbit_url` читається зі змінної RABBIT_URL. Якщо значення має
неправильний тип (наприклад, текст замість числа), сервіс впаде одразу при старті
з зрозумілою помилкою, а не десь посеред роботи.
"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Папка сервісу (…/ingest-service), щоб шлях до конфігу логів не залежав від того,
# з якої папки запущено сервіс.
SERVICE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    rabbit_url: str = "amqp://guest:guest@localhost:5672/"
    # Обмінник типу fanout: кожне повідомлення копіюється в черги recipes.mongo,
    # recipes.es і recipes.neo4j, які оголошують екземпляри writer-service.
    rabbit_exchange: str = "recipes"
    redis_url: str = "redis://localhost:6379/0"

    ingest_csv_path: str = "data/RAW_recipes.csv"
    # Швидкість за замовчуванням, поки користувач не змінив її на UI (записів/с).
    ingest_default_rate: int = 10
    # Період одного такту. 0,1 с замість 1 с, щоб при 5000 записів/с не було залпу
    # з 5000 повідомлень на початку кожної секунди.
    ingest_tick_seconds: float = 0.1

    log_config: Path = SERVICE_DIR / "config" / "logging.yaml"
