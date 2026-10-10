"""Повідомлення «рецепт прочитано з джерела»."""

from datetime import UTC, datetime
from uuid import uuid4

from pydantic import BaseModel, Field


class RecipePayload(BaseModel):
    """Дані одного рецепта в тому вигляді, в якому вони передаються через брокер.

    Поля відповідають колонкам набору Food.com (RAW_recipes.csv) після розбору:
    contributor_id -> chef_id, minutes -> cook_time_min, nutrition[0] -> calories.
    cook_time_min і calories дорівнюють None, якщо значення не пройшло правило очищення
    в ingest-service (час поза межами 1..10 080 хв, калорійність поза межами 0..20 000 ккал).
    """

    id: str
    title: str
    chef_id: str
    cuisine: str | None = None
    cook_time_min: int | None = None
    calories: float | None = None
    tags: list[str] = Field(default_factory=list)
    ingredients: list[str] = Field(default_factory=list)
    steps: list[str] = Field(default_factory=list)
    description: str = ""


class RecipeIngestedEvent(BaseModel):
    """Конверт повідомлення.

    event_id — унікальний ідентифікатор самого повідомлення. Потрібен, щоб writer-service
    міг розпізнати повторну доставку (RabbitMQ гарантує доставку «щонайменше один раз»).
    schema_version — версія формату повідомлення; збільшується, коли змінюється набір полів,
    щоб споживачі могли відрізнити старі повідомлення від нових.
    """

    event: str = "RecipeIngested"
    schema_version: int = 1
    event_id: str = Field(default_factory=lambda: uuid4().hex)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    recipe: RecipePayload
