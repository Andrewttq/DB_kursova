"""Перетворення повідомлення з брокера (контракт) на доменні об'єкти.

Навіщо окремий крок: формат повідомлення — це «зовнішній» контракт між сервісами,
а доменні класи — «внутрішня» модель. Якщо контракт зміниться, правимо лише тут,
а бізнес-логіка лишається незмінною.
"""

from contracts import RecipeIngestedEvent
from writer_service.domain.chef import Chef
from writer_service.domain.recipe import Recipe


def recipe_from_event(event: RecipeIngestedEvent) -> Recipe:
    raise NotImplementedError


def chef_from_event(event: RecipeIngestedEvent) -> Chef:
    """Згенерувати ім'я шефа з chef_id (наприклад, через random.Random(chef_id))."""
    raise NotImplementedError
