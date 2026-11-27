FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY contracts ./contracts
COPY ingest-service ./ingest-service
RUN uv sync --frozen --package ingest-service --no-dev
ENV PATH="/app/.venv/bin:$PATH"
CMD ["python", "-m", "ingest_service.main"]
