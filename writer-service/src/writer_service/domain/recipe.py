"""Доменні класи рецепта (ядро гексагона, без залежностей від бібліотек)."""

from dataclasses import dataclass, field


@dataclass
class Recipe:
    """Рецепт, як його бачить бізнес-логіка writer-service.

    id — стабільний ідентифікатор рецепта. Усі записи в БД виконуються
    як upsert за цим id, тому повторна доставка того самого повідомлення
    не створює дублікатів (ідемпотентність).
    """

    id: str
    title: str
    chef_id: str
    cuisine: str | None
    cook_time_min: int
    calories: float | None = None
    tags: list[str] = field(default_factory=list)
    ingredients: list[str] = field(default_factory=list)
    steps: list[str] = field(default_factory=list)
    description: str = ""
