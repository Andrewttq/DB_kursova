"""Повідомлення «рецепт прочитано з джерела»."""

from datetime import UTC, datetime
from uuid import uuid4

from pydantic import BaseModel, Field


class RecipePayload(BaseModel):
    """Дані одного рецепта в тому вигляді, в якому вони передаються через брокер.

    Поля відповідають колонкам набору Food.com (RAW_recipes.csv) після розбору:
    contributor_id -> chef_id, minutes -> cook_time_min, nutrition[0] -> calories.
    """

    id: str
    title: str
    chef_id: str
    cuisine: str | None = None
    cook_time_min: int
    calories: float | None = None
    tags: list[str] = Field(default_factory=list)
    ingredients: list[str] = Field(default_factory=list)
    steps: list[str] = Field(default_factory=list)
    description: str = ""


class RecipeIngestedEvent(BaseModel):
    """Конверт повідомлення.

    event_id — унікальний ідентифікатор самого повідомлення. Потрібен, щоб writer-service
    міг розпізнати повторну доставку (RabbitMQ гарантує доставку «щонайменше один раз»).
    """

    event: str = "RecipeIngested"
    event_id: str = Field(default_factory=lambda: uuid4().hex)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    recipe: RecipePayload
