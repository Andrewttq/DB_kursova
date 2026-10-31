FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY query-service ./query-service
RUN uv sync --frozen --package query-service --no-dev
ENV PATH="/app/.venv/bin:%PATH"
CMD ["uvicorn", "query_service.main:app", "--host", "0.0.0.0", "--port", "8000"]
