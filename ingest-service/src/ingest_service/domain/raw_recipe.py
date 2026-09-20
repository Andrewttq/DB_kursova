"""Доменний клас сервісу — рецепт у тому вигляді, як його прочитано з джерела.

Доменний шар — центр гексагона. Тут немає жодного імпорту бібліотек баз даних,
брокера чи веб-фреймворку: лише звичайні класи Python. Завдяки цьому бізнес-логіку
можна перевіряти тестами без запуску будь-якої інфраструктури.
"""

from dataclasses import dataclass, field


@dataclass
class RawRecipe:
    """Один рецепт після розбору рядка CSV.

    Відповідність колонкам RAW_recipes.csv:
        id             -> source_id
        name           -> title
        contributor_id -> chef_id
        minutes        -> cook_time_min
        nutrition[0]   -> calories   (nutrition зберігається як рядок-список)
        tags, ingredients, steps -> списки (теж рядки-списки, розбираються адаптером)
        description    -> description
    """

    source_id: str
    title: str
    chef_id: str
    cook_time_min: int
    calories: float | None = None
    tags: list[str] = field(default_factory=list)
    ingredients: list[str] = field(default_factory=list)
    steps: list[str] = field(default_factory=list)
    description: str = ""
