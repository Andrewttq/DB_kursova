"""Вихідний адаптер — читання налаштувань швидкості з Redis."""

from ingest_service.application.ports.outbound.ingest_config_port import IngestConfigPort


class RedisIngestConfigRepository(IngestConfigPort):
    """Реалізує IngestConfigPort.

    Налаштування зберігаються в хеші Redis `ingest:config`
    з полями `rate` і `running`. Записує їх query-service.
    Якщо ключа ще немає — повертати значення за замовчуванням.
    """

    def __init__(self, redis_url: str, default_rate: int) -> None:
        self._redis_url = redis_url
        self._default_rate = default_rate

    async def get_rate(self) -> int:
        raise NotImplementedError

    async def is_running(self) -> bool:
        raise NotImplementedError
