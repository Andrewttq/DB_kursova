"""Вихідний адаптер — метрики RabbitMQ через HTTP API плагіна management."""

import logging

import httpx

from query_service.application.ports.outbound.monitoring_ports import QueueMetricsPort

logger = logging.getLogger(__name__)


class RabbitQueueMetricsAdapter(QueueMetricsPort):
    """Реалізує QueueMetricsPort.

    Для кожної з трьох черг (recipes.mongo, recipes.es, recipes.neo4j):
    GET {management_url}/api/queues/%2F/{queue} -> поле "messages".
    (%2F — закодований virtual host "/".) Логін/пароль за замовчуванням guest/guest.
    Якщо RabbitMQ недоступний або черги ще немає — повертаємо 0 і пишемо WARNING у лог,
    щоб панель моніторингу не падала через одну метрику.
    """

    def __init__(
        self, client: httpx.AsyncClient, management_url: str, queue_names: list[str]
    ) -> None:
        self._client = client
        self._management_url = management_url.rstrip("/")
        self._queue_names = queue_names

    async def get_queue_depths(self) -> dict[str, int]:
        depths: dict[str, int] = {}
        for name in self._queue_names:
            url = f"{self._management_url}/api/queues/%2F/{name}"
            try:
                response = await self._client.get(url)
                if response.status_code == 404:
                    depths[name] = 0  # черга ще не оголошена (writer не запускався)
                    continue
                response.raise_for_status()
                depths[name] = int(response.json().get("messages", 0))
            except httpx.HTTPError as exc:
                logger.warning("RabbitMQ недоступний (%s), довжина черги %s = 0", exc, name)
                depths[name] = 0
        return depths
