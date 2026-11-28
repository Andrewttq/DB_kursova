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


def unique_by_title(recipes: list[Recipe]) -> list[Recipe]:
    """Генератор повторює датасет по колу (r-123, r-123-2, ...), тому в списках
    трапляються однакові рецепти. Лишаємо перший рецепт з кожною назвою."""
    seen: set[str] = set()
    result = []
    for r in recipes:
        if r.title not in seen:
            seen.add(r.title)
            result.append(r)
    return result


def recipe_to_short_dto(recipe: Recipe) -> RecipeShortDTO:
    return RecipeShortDTO(
        id=recipe.id,
        title=recipe.title,
        cuisine=recipe.cuisine,
        cook_time_min=recipe.cook_time_min,
        calories=recipe.calories,
    )


def recipe_to_card_dto(recipe: Recipe, chef_name: str) -> RecipeCardDTO:
    return RecipeCardDTO(
        id=recipe.id,
        title=recipe.title,
        cuisine=recipe.cuisine,
        cook_time_min=recipe.cook_time_min,
        calories=recipe.calories,
        tags=recipe.tags,
        chef_id=recipe.chef_id,
        chef_name=chef_name,
        ingredients=recipe.ingredients,
        steps=recipe.steps,
        description=recipe.description,
    )


def recommendation_to_dto(rec: Recommendation) -> RecommendationDTO:
    return RecommendationDTO(
        recipe_id=rec.recipe_id,
        title=rec.title,
        reason=f"спільних інгредієнтів: {rec.common_ingredients}",
    )


def hit_to_dto(hit: SearchHit) -> SearchHitDTO:
    return SearchHitDTO(
        recipe_id=hit.recipe_id, title=hit.title, snippet=hit.snippet, score=hit.score
    )


def log_entry_to_dto(entry: SearchLogEntry) -> SearchLogDTO:
    return SearchLogDTO(
        query=entry.raw_query,
        status="Знайдено" if entry.found else "Пусто",
        hits_count=entry.hits_count,
        from_cache=entry.from_cache,
        timestamp=entry.timestamp,
    )
