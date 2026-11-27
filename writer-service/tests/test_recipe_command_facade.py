"""Тести запису пачки: ролі, ідемпотентність, поведінка при помилці."""

import pytest
from writer_fakes import FakeChefs, FakeStats, FakeStore

from contracts import RecipeIngestedEvent, RecipePayload
from writer_service.application.facades.recipe_command_facade import RecipeCommandFacade
from writer_service.application.mappers import chef_name
from writer_service.application.services.chef_service import ChefService
from writer_service.application.services.recipe_services import (
    RecipeIndexService,
    RecipeInformationService,
    RecipeRelationService,
)
from writer_service.application.services.write_stats_service import WriteStatsService


def event(recipe_id: str, chef_id: str = "c-1") -> RecipeIngestedEvent:
    return RecipeIngestedEvent(
        recipe=RecipePayload(id=recipe_id, title=f"Recipe {recipe_id}", chef_id=chef_id)
    )


def make(role: str, broken: bool = False):
    store, chefs, stats = FakeStore(broken), FakeChefs(), FakeStats()
    facade = RecipeCommandFacade(
        role=role,
        recipes=RecipeInformationService(store),
        chefs=ChefService(chefs),
        relations=RecipeRelationService(store),
        index=RecipeIndexService(store),
        stats=WriteStatsService(stats),
    )
    return facade, store, chefs, stats


@pytest.mark.parametrize("role", ["mongo", "es", "neo4j"])
async def test_each_role_saves_batch_and_counts(role):
    facade, store, _, stats = make(role)
    saved = await facade.save_batch([event("r-1"), event("r-2")])
    assert saved == 2
    assert set(store.data) == {"r-1", "r-2"}
    assert stats.saved == 2


async def test_repeated_delivery_does_not_create_duplicates():
    facade, store, _, _ = make("mongo")
    await facade.save_batch([event("r-1")])
    await facade.save_batch([event("r-1")])  # RabbitMQ доставив те саме повторно
    assert len(store.data) == 1


async def test_chefs_are_deduplicated_within_batch():
    facade, _, chefs, _ = make("mongo")
    await facade.save_batch([event("r-1", "c-7"), event("r-2", "c-7"), event("r-3", "c-8")])
    assert chefs.calls == [2]


async def test_error_is_counted_and_reraised_so_message_is_not_acked():
    facade, _, _, stats = make("mongo", broken=True)
    with pytest.raises(ConnectionError):
        await facade.save_batch([event("r-1")])
    assert stats.failed == 1 and stats.saved == 0


def test_chef_name_is_deterministic():
    assert chef_name("c-42") == chef_name("c-42")
    assert chef_name("c-42") != chef_name("c-43")
