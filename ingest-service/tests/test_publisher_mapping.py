from ingest_service.adapters.outbound.rabbit_recipe_publisher import to_event
from ingest_service.domain.raw_recipe import RawRecipe


def test_raw_recipe_becomes_clean_event():
    raw = RawRecipe(
        source_id="137739",
        title="arriba baked winter squash",
        chef_id="47892",
        cook_time_min=0,
        calories=51.5,
        tags=["mexican", "easy"],
        ingredients=["winter squash", "honey"],
    )
    payload = to_event(raw).recipe
    assert payload.id == "r-137739"
    assert payload.chef_id == "c-47892"
    assert payload.cuisine == "mexican"
    assert payload.cook_time_min is None  # 0 хв -> помилка в даних
    assert payload.calories == 51.5
