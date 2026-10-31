"""Вхідний адаптер — перевірка зв'язку з Redis і MongoDB."""

import logging
from datetime import UTC, datetime

from fastapi import APIRouter
from pymongo import AsyncMongoClient
from redis.asyncio import Redis

log = logging.getLogger(__name__)


class HealthController:
    def __init__(self, redis: Redis, mongo: AsyncMongoClient) -> None:
        self._redis = redis
        self._mongo = mongo
        self.router = APIRouter(tags=["health"])
        self.router.add_api_route("/health", self.health, methods=["GET"])

    async def health(self) -> dict[str, str]:
        now = datetime.now(UTC).isoformat()
        await self._redis.set("health:last", now)
        raw = await self._redis.get("health:last")
        value = raw.decode() if isinstance(raw, bytes) else str(raw)
        await self._mongo.admin.command("ping")
        log.info("Redis: записано %s, прочитано %s, Mongo: ping ok", now, value)
        return {"mongo": "ok", "redis": "ok"}
