"""Контракти — формат повідомлень, якими обмінюються сервіси через RabbitMQ.

Чому окремий пакет: ingest-service публікує повідомлення, writer-service їх читає.
Якщо формат описати двічі (у кожному сервісі окремо), рано чи пізно описи розійдуться
і writer перестане розуміти ingest. Тому формат описано один раз, а обидва сервіси
підключають цей пакет як залежність.
"""

from contracts.recipe_events import RecipeIngestedEvent, RecipePayload

__all__ = ["RecipeIngestedEvent", "RecipePayload"]
