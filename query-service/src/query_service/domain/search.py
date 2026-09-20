"""Доменні класи пошуку."""

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class SearchHit:
    """Один знайдений рецепт.

    snippet — фрагмент тексту, де знайдені слова обгорнуто в <em>...</em>
    (підсвічування від Elasticsearch, вимога методички).
    """

    recipe_id: str
    title: str
    snippet: str
    score: float


@dataclass
class SearchLogEntry:
    """Запис журналу пошуку для блоку «Останні запити» на UI."""

    raw_query: str
    normalized_key: str
    hits_count: int
    from_cache: bool
    took_ms: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def found(self) -> bool:
        """Статус для UI: «Знайдено» / «Пусто»."""
        return self.hits_count > 0
