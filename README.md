# Recipes Hub

[Українська](#українська) ·  [English](#english)
- Іван - зона A, github - @ivan0950
---

## Українська

Курсова робота з дисципліни «Бази даних та інформаційні системи», варіант 6 «Кулінарні рецепти та шеф-кухарі».
Розподілена система збору, зберігання, повнотекстового пошуку та моніторингу рецептів.

### Архітектура

Три мікросервіси (Python 3.12, FastAPI, asyncio), кожен усередині побудований за гексагональною архітектурою; CQRS реалізовано на рівні сервісів.

```
CSV (Food.com) → ingest-service → RabbitMQ → writer-service → MongoDB (3 шарди) / Neo4j / Elasticsearch
                                                                       ↑
                         браузер (HTMX) ⇄ query-service ⇄ Redis (кеш, статистика)
```

| Сервіс | Роль |
|---|---|
| `ingest-service` | Читає рецепти з CSV із заданою швидкістю (10–5000/с) і публікує в RabbitMQ |
| `writer-service` | Command: забирає повідомлення пачками і записує в MongoDB, Neo4j, Elasticsearch |
| `query-service` | Query: пошук, картки рецептів, рекомендації, статистика, веб-інтерфейс |
| `contracts` | Спільний формат повідомлень між сервісами |

Структура кожного сервісу:

```
src/<service>/
  domain/                  доменні класи
  application/
    dto.py                 DTO (лише query-service)
    ports/inbound/         вхідні порти (*UseCase)
    ports/outbound/        вихідні порти (*Repository, *Port)
    services/              прикладні сервіси
    facades/               фасади (реалізують вхідні порти)
  adapters/
    inbound/               контролери, споживач RabbitMQ, планувальник
    outbound/              MongoDB, Elasticsearch, Neo4j, Redis, RabbitMQ, CSV
  container.py             збирання залежностей
  main.py                  точка входу
```

### Початок роботи

Потрібно: Git, [uv](https://docs.astral.sh/uv/getting-started/installation/), Docker Desktop (з етапу підключення БД).

```bash
git clone <url> && cd recipes-hub
uv sync --all-packages          # встановить Python 3.12 і всі залежності
uv run pre-commit install       # перевірка коду перед кожним комітом
cp .env.example .env            # Windows: copy .env.example .env
```

Запуск сервісів (з кореня репозиторію):

```bash
uv run --package query-service uvicorn query_service.main:app --reload
uv run --package writer-service python -m writer_service.main
uv run --package ingest-service python -m ingest_service.main
```

Веб-інтерфейс: http://localhost:8000 · документація API: http://localhost:8000/docs

Набір даних: [Food.com Recipes and Interactions](https://www.kaggle.com/datasets/shuyangli94/food-com-recipes-and-user-interactions) — файл `RAW_recipes.csv` покласти в `data/`.

### Правила роботи в команді

- Гілка `main` захищена, зміни лише через Pull Request.
- Одна задача — одна гілка: `feature/es-search`, `fix/cache-key`.
- Кожен PR переглядає не автор.
- Коміти за [Conventional Commits](https://www.conventionalcommits.org/): `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`.

---

## English

Coursework for "Databases and Information Systems", topic 6 "Recipes and Chefs".
A distributed system for ingesting, storing, full-text searching and monitoring recipes.

### Architecture

Three microservices (Python 3.12, FastAPI, asyncio), each built internally with hexagonal architecture; CQRS is applied at the service level.

| Service | Role |
|---|---|
| `ingest-service` | Reads recipes from CSV at a configurable rate (10–5000/s) and publishes them to RabbitMQ |
| `writer-service` | Command side: consumes messages in batches and writes to MongoDB, Neo4j, Elasticsearch |
| `query-service` | Query side: search, recipe cards, recommendations, statistics, web UI |
| `contracts` | Shared message format between services |

Storage: MongoDB (sharded, 3 shards) for recipe documents, Elasticsearch for full-text search, Neo4j for chef–recipe–ingredient relations and recommendations, Redis for search cache and statistics, RabbitMQ as the message broker.

### Getting started

Requirements: Git, [uv](https://docs.astral.sh/uv/getting-started/installation/), Docker Desktop.

```bash
git clone <url> && cd recipes-hub
uv sync --all-packages
uv run pre-commit install
cp .env.example .env
uv run --package query-service uvicorn query_service.main:app --reload
```

UI: http://localhost:8000 · API docs: http://localhost:8000/docs

Dataset: [Food.com Recipes and Interactions](https://www.kaggle.com/datasets/shuyangli94/food-com-recipes-and-user-interactions) — put `RAW_recipes.csv` into `data/`.

### Team workflow

Protected `main`, feature branches, every PR reviewed by someone other than the author, Conventional Commits.
