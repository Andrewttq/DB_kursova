from query_service.application.services.search_services import QueryNormalizer

n = QueryNormalizer()
NO_FILTERS = {"cuisine": None, "max_cook_time_min": None, "max_calories": None}


def key(q: str, **filters) -> str:
    return n.cache_key(q, {**NO_FILTERS, **filters}, 1, 10)


def test_word_order_case_and_punctuation_do_not_matter():
    assert key("Chicken Garlic Pasta") == key("pasta, garlic chicken!")


def test_duplicates_are_removed():
    assert n.normalize("chicken chicken") == "chicken"


def test_plural_gives_same_key():
    assert key("chickens") == key("chicken")


def test_short_words_and_double_s_are_not_stemmed():
    assert n.normalize("gas bass") == "bass gas"


def test_different_filters_give_different_keys():
    assert key("chicken", cuisine="italian") != key("chicken", cuisine="mexican")


def test_page_is_part_of_key():
    f = NO_FILTERS
    assert n.cache_key("chicken", f, 1, 10) != n.cache_key("chicken", f, 2, 10)


def test_empty_query_does_not_crash():
    assert n.normalize("  ,,, ") == ""
    assert key("").startswith("search:")
