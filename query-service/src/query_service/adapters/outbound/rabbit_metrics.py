"""Вихідний адаптер — метрики RabbitMQ через HTTP API плагіна management."""

import httpx

from query_service.application.ports.outbound.monitoring_ports import QueueMetricsPort


class RabbitQueueMetricsAdapter(QueueMetricsPort):
    """Реалізує QueueMetricsPort.

    Для кожної з трьох черг (recipes.mongo, recipes.es, recipes.neo4j):
    GET {management_url}/api/queues/%2F/{queue} -> поле "messages".
    (%2F — закодований virtual host "/".) Логін/пароль за замовчуванням guest/guest.
    Якщо RabbitMQ недоступний — повертати 0 і писати WARNING у лог,
    щоб панель моніторингу не падала через одну метрику.
    """

    def __init__(
        self, client: httpx.AsyncClient, management_url: str, queue_names: list[str]
    ) -> None:
        self._client = client
        self._management_url = management_url
        self._queue_names = queue_names

    async def get_queue_depths(self) -> dict[str, int]:
        raise NotImplementedError
