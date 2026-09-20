"""Точка входу query-service (FastAPI).

Запуск (з кореня репозиторію):
    uv run --package query-service uvicorn query_service.main:app --reload
Після запуску:
    http://localhost:8000       — веб-інтерфейс
    http://localhost:8000/docs  — автоматична документація API (Swagger)
"""

import logging.config
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import yaml
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from query_service.container import build_container
from query_service.settings import Settings

settings = Settings()
with open(settings.log_config, encoding="utf-8") as f:
    logging.config.dictConfig(yaml.safe_load(f))

container = build_container(settings)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Код до yield виконується при старті, після — при зупинці сервісу."""
    yield
    await container.close()


app = FastAPI(title="Recipes Hub — query-service", lifespan=lifespan)
for router in container.routers:
    app.include_router(router)


@app.exception_handler(NotImplementedError)
async def not_implemented_handler(_: Request, __: NotImplementedError) -> JSONResponse:
    """Поки методи-заглушки не реалізовано, повертаємо 501 замість 500."""
    return JSONResponse(status_code=501, content={"detail": "Ще не реалізовано"})
