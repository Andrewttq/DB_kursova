"""Доменний клас шеф-кухаря."""

from dataclasses import dataclass


@dataclass
class Chef:
    """Автор рецепта.

    У наборі Food.com автор відомий лише як contributor_id, тому ім'я
    генерується детерміновано з id (один id -> завжди одне ім'я).
    """

    id: str
    full_name: str
