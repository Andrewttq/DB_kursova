"""DTO (Data Transfer Objects) — моделі даних на межі сервісу.

DTO описують, що приходить у запиті та що повертається у відповіді API.
Вони відокремлені від доменних класів навмисно: можна змінити формат відповіді
для UI, не чіпаючи бізнес-логіку, і навпаки. Pydantic автоматично перевіряє
вхідні дані (типи, межі значень) і генерує документацію API (/docs).
"""

from datetime import datetime

from pydantic import BaseModel, Field

# ---------- Рецепти ----------


class RecipeShortDTO(BaseModel):
    """Коротка картка для списків."""

    id: str
    title: str
    cuisine: str | None
    cook_time_min: int
    calories: float | None


class RecipeCardDTO(RecipeShortDTO):
    """Повна картка рецепта."""

    chef_id: str
    chef_name: str
    ingredients: list[str]
    steps: list[str]
    description: str
    tags: list[str]


class RecipeFilterDTO(BaseModel):
    """Параметри фільтрації списку рецептів."""

    cuisine: str | None = None
    max_cook_time_min: int | None = Field(default=None, ge=1)
    max_calories: float | None = Field(default=None, ge=0)
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)


class RecommendationDTO(BaseModel):
    recipe_id: str
    title: str
    reason: str  # наприклад, «спільних інгредієнтів: 5»


# ---------- Шефи ----------


class ChefDTO(BaseModel):
    id: str
    full_name: str


class ChefProfileDTO(ChefDTO):
    recipes: list[RecipeShortDTO]


# ---------- Пошук ----------


class SearchRequestDTO(BaseModel):
    query: str = Field(min_length=1, max_length=200)
    cuisine: str | None = None
    max_cook_time_min: int | None = Field(default=None, ge=1)
    size: int = Field(default=10, ge=1, le=50)


class SearchHitDTO(BaseModel):
    recipe_id: str
    title: str
    snippet: str
    score: float


class SearchResponseDTO(BaseModel):
    query: str
    normalized_key: str
    from_cache: bool
    took_ms: float
    hits: list[SearchHitDTO]


class SearchLogDTO(BaseModel):
    query: str
    status: str  # «Знайдено» / «Пусто»
    hits_count: int
    from_cache: bool
    timestamp: datetime


# ---------- Моніторинг ----------


class IngestConfigDTO(BaseModel):
    """Значення слайдера та перемикача Старт/Стоп."""

    rate_per_sec: int = Field(ge=10, le=5000)
    running: bool = True


class StatsDTO(BaseModel):
    read_total: int
    published_total: int
    saved_total: int
    failed_total: int
    write_rps: float
    queue_depth: int
    recent_searches: list[SearchLogDTO]
