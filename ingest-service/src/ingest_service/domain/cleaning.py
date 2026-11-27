"""Правила очищення даних набору Food.com (див. розділ 2 звіту).

Чисті функції без залежностей від бібліотек: їх легко перевірити тестами.
Застосовуються в ingest-service перед публікацією, тому в брокер (а значить, і в усі
три сховища) потрапляють уже очищені дані.
"""

from ingest_service.domain.cuisines import CUISINES

MAX_COOK_TIME_MIN = 10_080  # тиждень; більші значення в наборі — помилки введення
MAX_CALORIES = 20_000

# Широкі регіони: якщо в рецепта є і "asian", і "thai", інформативніша саме "thai".
BROAD_CUISINES = {"american", "asian", "european", "african", "middle-eastern"}


def clean_cook_time(minutes: int | None) -> int | None:
    """Час поза межами 1..10 080 хв вважаємо помилковим -> None (невідомо)."""
    if minutes is None or not 1 <= minutes <= MAX_COOK_TIME_MIN:
        return None
    return minutes


def clean_calories(calories: float | None) -> float | None:
    """Калорійність поза межами (0; 20 000] ккал -> None. Нуль теж помилка: їжа без калорій."""
    if calories is None or not 0 < calories <= MAX_CALORIES:
        return None
    return calories


def pick_cuisine(tags: list[str]) -> str | None:
    """Кухня рецепта з його тегів.

    У наборі немає окремого поля «кухня», вона є серед тегів. Якщо збігається кілька
    тегів, обираємо найконкретніший: спочатку вузькі кухні (italian, thai), і лише якщо
    їх немає — широкий регіон (asian, american). Порядок усередині групи — як у CUISINES.
    """
    matched = [c for c in CUISINES if c in set(tags)]
    specific = [c for c in matched if c not in BROAD_CUISINES]
    if specific:
        return specific[0]
    return matched[0] if matched else None


def recipe_id(source_id: str) -> str:
    return f"r-{source_id}"


def chef_id(contributor_id: str) -> str:
    return f"c-{contributor_id}"
