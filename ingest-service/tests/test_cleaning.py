from ingest_service.domain.cleaning import clean_calories, clean_cook_time, pick_cuisine


def test_cook_time_bounds():
    assert clean_cook_time(30) == 30
    assert clean_cook_time(0) is None
    assert clean_cook_time(10_081) is None
    assert clean_cook_time(10_080) == 10_080


def test_calories_bounds():
    assert clean_calories(250.5) == 250.5
    assert clean_calories(0) is None  # нуль — помилка введення
    assert clean_calories(20_001) is None


def test_specific_cuisine_wins_over_region():
    assert pick_cuisine(["easy", "asian", "thai"]) == "thai"
    assert pick_cuisine(["dinner", "american"]) == "american"
    assert pick_cuisine(["dessert"]) is None
