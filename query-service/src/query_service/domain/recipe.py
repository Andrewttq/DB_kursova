"""Доменний клас рецепта для читання.

Зверніть увагу: у writer-service теж є клас Recipe. Це нормально для мікросервісів —
кожен сервіс має власну модель під свої задачі і не залежить від коду іншого.
Спільним є лише контракт повідомлень (пакет contracts).
"""

from dataclasses import dataclass, field


@dataclass
class Recipe:
    id: str
    title: str
    chef_id: str
    cuisine: str | None
    cook_time_min: int | None = None  # None = час невідомий або помилковий
    calories: float | None = None
    tags: list[str] = field(default_factory=list)
    ingredients: list[str] = field(default_factory=list)
    steps: list[str] = field(default_factory=list)
    description: str = ""


@dataclass
class Recommendation:
    """Рецепт-рекомендація з поясненням, чому його запропоновано.

    common_ingredients — кількість спільних інгредієнтів (показується користувачу);
    score — сума 1 / recipe_count за спільними інгредієнтами, за нею впорядковано видачу.
    """

    recipe_id: str
    title: str
    common_ingredients: int
    score: float
