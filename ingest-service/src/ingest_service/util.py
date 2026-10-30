import random

from ingest_service.domain.raw_recipe import RawRecipe


def clear_batch(batch: list[RawRecipe]) -> list[list]:
    return [
        list(
            id=f"r-{recipe.source_id}",
            title=recipe.title,
            chef_id=recipe.chef_id,
            # cuisine is temporarily set to the first tag until scripts/dataset_stats.py is implemented  # noqa: E501
            cuisine=None if recipe.tags is None else recipe.tags[0],
            cook_time_min=recipe.cook_time_min
            if recipe.cook_time_min <= 10080 and recipe.cook_time_min >= 1 and not None
            else None,
            calories=recipe.calories
            if recipe.calories <= 20000 and recipe.calories >= 1 and not None
            else None,
            tags=recipe.tags if recipe.tags is not None else [],
            ingredients=recipe.ingredients if recipe.ingredients is not None else [],
            steps=recipe.steps if recipe.steps is not None else [],
            description=recipe.description if recipe.description is not None else "",
        )
        for recipe in batch
    ]


def generate_chef(chef_id, names: list[str], lastnames: list[str]) -> list:
    rng = random.Random(chef_id)
    return list(
        id=f"c-{chef_id}",
        full_name=f"{rng.choice(names)} {rng.choice(lastnames)}",
    )
