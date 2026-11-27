"""Тести ланцюжка завдання 12 (фасад -> сервіси -> порти) з фейковими репозиторіями."""

from query_fakes import RECOMMENDATION, FakeChefs, FakeGraph, FakeRecipes

from query_service.application.dto import RecipeFilterDTO
from query_service.application.facades.chef_query_facade import ChefQueryFacade
from query_service.application.facades.recipe_query_facade import RecipeQueryFacade
from query_service.application.services.chef_service import ChefService
from query_service.application.services.recipe_services import (
    RecipeInformationService,
    RecipeRelationService,
)
from query_service.domain.recipe import Recipe

RECIPES = [
    Recipe(id="r1", title="Borscht", chef_id="c1", cuisine="ukrainian", cook_time_min=90),
    Recipe(id="r2", title="Pasta", chef_id="c1", cuisine="italian", cook_time_min=20),
    Recipe(id="r3", title="Pizza", chef_id="c2", cuisine="italian", cook_time_min=40),
]


def facades(graph: FakeGraph | None = None):
    graph = graph or FakeGraph(similar=[RECOMMENDATION], chef_recipes=["r2", "r1"])
    recipes = RecipeInformationService(FakeRecipes(RECIPES))
    chefs = ChefService(FakeChefs())
    relations = RecipeRelationService(graph)
    return (
        RecipeQueryFacade(recipes=recipes, chefs=chefs, relations=relations),
        ChefQueryFacade(chefs=chefs, relations=relations, recipes=recipes),
    )


async def test_card_contains_chef_name():
    card = await facades()[0].get_recipe_card("r1")
    assert card.chef_name == "Olena Kovalenko"
    assert card.title == "Borscht"


async def test_missing_recipe_returns_none():
    assert await facades()[0].get_recipe_card("nope") is None


async def test_filter_and_paging():
    facade = facades()[0]
    page1 = await facade.list_recipes(RecipeFilterDTO(cuisine="italian", size=1, page=1))
    page2 = await facade.list_recipes(RecipeFilterDTO(cuisine="italian", size=1, page=2))
    assert [r.id for r in page1] == ["r2"]
    assert [r.id for r in page2] == ["r3"]


async def test_recommendations_have_reason():
    recs = await facades()[0].get_recommendations("r1", 5)
    assert recs[0].reason == "спільних інгредієнтів: 3"


async def test_broken_graph_does_not_break_page():
    recipe_facade, chef_facade = facades(FakeGraph(broken=True))
    assert await recipe_facade.get_recommendations("r1", 5) == []
    profile = await chef_facade.get_chef_profile("c1")
    # граф недоступний -> рецепти взяті напряму з MongoDB
    assert {r.id for r in profile.recipes} == {"r1", "r2"}


async def test_chef_profile_keeps_graph_order():
    profile = await facades()[1].get_chef_profile("c1")
    assert [r.id for r in profile.recipes] == ["r2", "r1"]


async def test_unknown_chef_returns_none():
    assert await facades()[1].get_chef_profile("nobody") is None
