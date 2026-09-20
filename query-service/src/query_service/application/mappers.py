"""Перетворення доменних об'єктів на DTO для відповіді API."""

from query_service.application.dto import (
    RecipeCardDTO,
    RecipeShortDTO,
    RecommendationDTO,
    SearchHitDTO,
    SearchLogDTO,
)
from query_service.domain.recipe import Recipe, Recommendation
from query_service.domain.search import SearchHit, SearchLogEntry


def recipe_to_short_dto(recipe: Recipe) -> RecipeShortDTO:
    raise NotImplementedError


def recipe_to_card_dto(recipe: Recipe, chef_name: str) -> RecipeCardDTO:
    raise NotImplementedError


def recommendation_to_dto(rec: Recommendation) -> RecommendationDTO:
    raise NotImplementedError


def hit_to_dto(hit: SearchHit) -> SearchHitDTO:
    raise NotImplementedError


def log_entry_to_dto(entry: SearchLogEntry) -> SearchLogDTO:
    raise NotImplementedError
