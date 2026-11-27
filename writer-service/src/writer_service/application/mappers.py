"""Перетворення повідомлення з брокера (контракт) на доменні об'єкти.

Навіщо окремий крок: формат повідомлення — це «зовнішній» контракт між сервісами,
а доменні класи — «внутрішня» модель. Якщо контракт зміниться, правимо лише тут,
а бізнес-логіка лишається незмінною.
"""

from faker import Faker

from contracts import RecipeIngestedEvent
from writer_service.domain.chef import Chef
from writer_service.domain.recipe import Recipe

# Один екземпляр на весь процес: створення Faker повільне.
_faker = Faker("en_US")


def recipe_from_event(event: RecipeIngestedEvent) -> Recipe:
    p = event.recipe
    return Recipe(
        id=p.id,
        title=p.title,
        chef_id=p.chef_id,
        cuisine=p.cuisine,
        cook_time_min=p.cook_time_min,
        calories=p.calories,
        tags=list(p.tags),
        ingredients=list(p.ingredients),
        steps=list(p.steps),
        description=p.description,
    )


def chef_name(chef_id: str) -> str:
    """Детерміноване ім'я: генератор ініціалізується значенням chef_id,
    тому один і той самий id завжди дає те саме ім'я (і в усіх екземплярах сервісу)."""
    _faker.seed_instance(chef_id)
    return _faker.name()


def chef_from_event(event: RecipeIngestedEvent) -> Chef:
    """Згенерувати ім'я шефа з chef_id (у наборі Food.com є лише contributor_id)."""
    return Chef(id=event.recipe.chef_id, full_name=chef_name(event.recipe.chef_id))
